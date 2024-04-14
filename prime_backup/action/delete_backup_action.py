from typing import Optional, NamedTuple, List

from prime_backup.action import Action
from prime_backup.db.access import DbAccess
from prime_backup.types.backup_info import BackupInfo
from prime_backup.types.blob_info import BlobInfo, BlobListSummary
from prime_backup.types.units import ByteCount
from prime_backup.utils import collection_utils, misc_utils


class BlobTrashBin(List[BlobInfo]):
	def __init__(self):
		super().__init__()

	def make_summary(self) -> BlobListSummary:
		return BlobListSummary.of(self)

	def erase_all(self):
		for trash in self:
			trash.blob_path.unlink()


class DeleteOrphanBlobsAction(Action[BlobListSummary]):
	def __init__(self, blob_hash_to_check: Optional[List[str]], quiet: bool = False):
		super().__init__()
		self.blob_hash_to_check = blob_hash_to_check
		if self.blob_hash_to_check is not None:
			self.blob_hash_to_check = collection_utils.deduplicated_list(self.blob_hash_to_check)
		self.quiet = quiet

	def run(self) -> BlobListSummary:
		trash_bin = BlobTrashBin()

		if not self.quiet:
			self.logger.info('Delete orphan blobs start')
		with DbAccess.open_session() as session:
			if self.blob_hash_to_check is None:
				hashes = session.get_all_blob_hashes()
			else:
				hashes = self.blob_hash_to_check

			orphan_blob_hashes = session.filtered_orphan_blob_hashes(hashes)
			orphan_blobs = session.get_blobs(orphan_blob_hashes)

			for blob in orphan_blobs.values():
				trash_bin.append(BlobInfo.of(blob))
			session.delete_blobs(list(orphan_blobs.keys()))

		s = trash_bin.make_summary()
		trash_bin.erase_all()
		if not self.quiet:
			self.logger.info('Delete orphan blobs done, erasing blobs (count {}, size {} / {})'.format(
				s.count, ByteCount(s.stored_size).auto_str(), ByteCount(s.raw_size).auto_str(),
			))
		return s


class DeleteBackupResult(NamedTuple):
	backup: BackupInfo
	bls: BlobListSummary


class DeleteBackupAction(Action[DeleteBackupResult]):
	def __init__(self, backup_id: int):
		super().__init__()
		self.backup_id = misc_utils.ensure_type(backup_id, int)

	def run(self) -> DeleteBackupResult:
		self.logger.info('Deleting backup #{}'.format(self.backup_id))
		with DbAccess.open_session() as session:
			backup = session.get_backup(self.backup_id)
			info = BackupInfo.of(backup)

			hashes = []
			for file in session.get_backup_files(backup.id):
				if file.blob_hash is not None:
					hashes.append(file.blob_hash)
				session.delete_file(file)
			session.delete_backup(backup)

		# TODO: orphan_file_cleaner
		orphan_blob_cleaner = DeleteOrphanBlobsAction(hashes, quiet=True)
		bls = orphan_blob_cleaner.run()

		self.logger.info('Deleted backup #{} done, -{} blobs (size {} / {})'.format(
			info.id, bls.count, ByteCount(bls.stored_size).auto_str(), ByteCount(bls.raw_size).auto_str(),
		))
		return DeleteBackupResult(info, bls)
