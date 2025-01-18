import functools
from abc import ABC
from pathlib import Path
from typing import List, Callable, Optional

from typing_extensions import override, Unpack

from prime_backup.action import Action
from prime_backup.action.helpers.fileset_allocator import FilesetAllocator, FilesetAllocateArgs
from prime_backup.db import schema
from prime_backup.db.session import DbSession
from prime_backup.types.backup_info import BackupInfo
from prime_backup.types.blob_info import BlobInfo, BlobListSummary


class CreateBackupActionBase(Action[BackupInfo], ABC):
	def __init__(self):
		super().__init__()
		self.__new_blobs: List[BlobInfo] = []
		self.__new_blobs_summary: Optional[BlobListSummary] = None
		self.__blobs_rollbackers: List[Callable] = []

	def _remove_file(self, file_to_remove: Path, *, what: str = 'rollback'):
		try:
			file_to_remove.unlink(missing_ok=True)
		except OSError as e:
			self.logger.error('({}) remove file {!r} failed: {}'.format(what, file_to_remove, e))

	def _add_remove_file_rollbacker(self, file_to_remove: Path):
		self.__blobs_rollbackers.append(functools.partial(self._remove_file, file_to_remove=file_to_remove))

	def _apply_blob_rollback(self):
		if len(self.__blobs_rollbackers) > 0:
			self.logger.warning('Error occurs during backup creation, applying rollback')
			for rollback_func in self.__blobs_rollbackers:
				rollback_func()
			self.__blobs_rollbackers.clear()

	def _create_blob(self, session: DbSession, **kwargs: Unpack[DbSession.CreateBlobKwargs]) -> schema.Blob:
		blob = session.create_and_add_blob(**kwargs)
		self.__new_blobs.append(BlobInfo.of(blob))
		return blob

	def get_new_blobs_summary(self) -> BlobListSummary:
		if self.__new_blobs_summary is None:
			self.__new_blobs_summary = BlobListSummary.of(self.__new_blobs)
		return self.__new_blobs_summary

	def _finalize_backup_and_files(self, session: DbSession, backup: schema.Backup, files: List[schema.File]):
		allocate_args = FilesetAllocateArgs.from_config(self.config)
		allocate_result = FilesetAllocator(session, files).allocate(allocate_args)
		fs_base, fs_delta = allocate_result.fileset_base, allocate_result.fileset_delta

		backup.fileset_id_base = fs_base.id
		backup.fileset_id_delta = fs_delta.id
		backup.file_count = fs_base.file_count + fs_delta.file_count
		backup.file_raw_size_sum = fs_base.file_raw_size_sum + fs_delta.file_raw_size_sum
		backup.file_stored_size_sum = fs_base.file_stored_size_sum + fs_delta.file_stored_size_sum

		session.add(backup)
		session.flush()  # this generates backup.id

	@override
	def run(self) -> None:
		self.__new_blobs.clear()
		self.__new_blobs_summary = None
		self.__blobs_rollbackers.clear()
