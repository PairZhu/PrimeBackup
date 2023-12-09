---
title: '配置文件'
---

## 配置文件详解

这是对配置文件的完整解释。如果你想深入了解它，那就接着往下看吧

### 根配置

这是配置文件中的根 json 对象

```json
{
    "enabled": true,
    "debug": false,
    "storage_root": "./pb_files",
    
    // 子配置。详见以下各节
    "command": {/* 命令配置 */},
    "server": {/* 服务器配置 */},
    "backup": {/* 备份配置 */},
    "scheduled_backup": {/* 定时备份配置 */},
    "prune": {/* 修剪配置 */},
    "database": {/* 数据库配置 */}
}
```

#### enabled

插件的开关。设置为 `false` 以禁用插件

- 类型：`bool`
- 默认值：`false`

#### debug

调试开关。设置为 `true` 以启用调试日志

- 类型：`bool`
- 默认值：`false`

#### storage_root

Prime Backup 储存各种数据文件所用的根目录

这是一个相对于 MCDR 工作目录的相对路径。默认情况下，根目录将是 `/path/to/mcdr_root/pb_files`

- 类型：`str`
- 默认值：`"./pb_files"`

---

### 命令配置

```json
{
    "prefix": "!!pb",
    "permission": {
        "abort": 1,  
        "back": 2,
        "confirm": 1,
        "database": 4,
        "delete": 2,
        "delete_range": 3,
        "export": 4,
        "list": 1,
        "make": 1,
        "prune": 3,
        "rename": 2,
        "show": 1,
        "tag": 3
    },
    "confirm_time_wait": "1m",
    "backup_on_restore": true,
    "restore_countdown_sec": 10
}
```

#### prefix

MCDR 中，Prime Backup 所有命令的前缀。通常你不需要更改它

- 类型：`str`
- 默认值：`"!!pb"`

#### permission

所有子命令所需的 [MCDR 权限等级](https://mcdreforged.readthedocs.io/en/latest/permission.html) 的最低要求

它是一个从字符串映射到整数的映射表，存储所有子命令的权限级别要求。
如果子命令不在映射表中，将使用 `1` 作为默认的权限等级要求

例如，在默认配置中，`"back"` 被映射到 `2`，
这意味着 `!!pb back` 命令需要权限级别 >=2 才能执行。

- 类型：`Dict[str, int]`

#### confirm_time_wait

有一些命令需要用户输入 `!!pb confirm` 才可继续执行。
这里定义了这些命令的最长等待时间

若等待超时，则命令将被取消执行

- 类型：[`Duration`](#duration)
- 默认值：`"1m"`

#### backup_on_restore

在回档至指定备份前，是否要自动创建一个备份。这一类备份被称为“回档前备份”

这是一道为那些傻瓜用户准备的安全保障

- 类型：`bool`
- 默认值：`true`

#### restore_countdown_sec

在回档时，关闭 Minecraft 服务器前，执行倒计时的持续秒数

- 类型：`int`
- 默认值：`10`

---

### 服务器配置

与 Minecraft 服务器交互相关的选项

```json
{
    "turn_off_auto_save": true,
    "commands": {
        "save_all_worlds": "save-all flush",
        "auto_save_off": "save-off",
        "auto_save_on": "save-on"
    },
    "saved_world_regex": [
        "^Saved the game$",
        "^Saved the world$"
    ],
    "save_world_max_wait": "10m"
}
```

#### turn_off_auto_save

是否应在进行备份之前关闭自动保存

由于关闭自动保存可以确保在备份期间，Minecraft 存档文件不会发生变化，因此建议将此选项设置为 `true`

- 类型：`bool`
- 默认值：`true`

#### commands

Prime Backup 使用的 Minecraft 指令的集合。目前它们仅在创建备份期间使用

Prime Backup 在创建备份时的操作时序如下：

1. 如果配置 [`turn_off_auto_save`](#turn_off_auto_save) 为 `true`，则使用子配置 `auto_save_off` 存储的命令关闭自动保存
2. 使用子配置 `save_all_worlds` 存储的命令，触发服务器保存
3. 等待直到世界保存完毕，即服务器输出与 [`saved_world_regex`](#saved_world_regex) 的某一个正则表达式成功匹配
4. 创建备份
5. 如果配置 [`turn_off_auto_save`](#turn_off_auto_save) 为 `true`，则使用子配置 `auto_save_on` 存储的命令打开自动保存

#### saved_world_regex

一个正则表达式列表，用于识别服务器是否已保存完成

- 类型：`List[re.Pattern]`

#### save_world_max_wait

在创建备份期间，等待世界保存完成的最长等待时间

- 类型：[`Duration`](#duration)
- 默认值：`"10m"`

---

### 备份配置

与创建配置具体细节相关的配置

```json
{
    "source_root": "./server",
    "targets": [
        "world"
    ],
    "ignored_files": [
        "session.lock"
    ],
    "hash_method": "xxh128",
    "compress_method": "zstd",
    "compress_threshold": 64
}
```

#### source_root

进行备份/还原操作的根目录

通常应该是 MCDR 的 [工作目录](https://mcdreforged.readthedocs.io/zh-cn/latest/configuration.html#working-directory)，
即默认情况下的 `server` 目录

- 类型：`str`
- 默认值：`"./server"`

#### targets

要备份的目标文件/目录

通常来讲，你需要在整理添加你的存档文件夹的名字

例如，对于像 bukkit 那样把每个维度存在独立的文件夹里的服务器，你需要这么配置：

```json
"targets": [
    "world",
    "world_nether",
    "world_the_end"
]
```

- 类型：`List[str]`

#### ignored_files

在备份时忽略的文件名列表，默认仅包含 `session.lock` 
以解决 Windows 下 `session.lock` 被服务端占用导致备份失败的问题

若文件名字符串以 `*` 开头，则将忽略以指定字符串结尾的文件，
如 `*.test` 表示忽略所有以 `.test` 结尾的文件，如 `a.test`

若文件名字符串以 `*` 结尾，则将忽略以指定字符串开头的文件，
如 `temp*` 表示忽略所有以 `temp` 开头的文件，如 `tempfile`

- 类型：`List[str]`

#### hash_method

对文件进行哈希时所使用的算法。可用选项：`"xxh128"`、`"sha256"`

- [`"xxh128"`](https://github.com/Cyan4973/xxHash): A extremely fast, high-quality 128bit non-cryptographic hash algorithm. 
  Recommend to use, unless you want theoretic extreme safety on hackers
- [`"sha256"`](https://en.wikipedia.org/wiki/SHA-2): A cryptographically secure and widely used 256bit hash algorithm.
  It's slower than xxh128, but the speed is acceptable enough with modern hardware


!!! danger

    你 **不能** 在启用插件后修改 `hash_method`。请明智地做出选择

    如果你确实需要修改 `hash_method`，你需要删除 [数据根目录](#storage_root) 路径下的 `prime_backup.db` 文件和 `blobs` 文件夹。
    这将删除所有的备份

- 类型：`str`
- 默认值：`"xxh128"`

#### compress_method

在储存备份中的文件时，所使用的压缩方法

| 压缩方法    | 描述                                                                                                    | 速度    | 压缩率   |
|---------|-------------------------------------------------------------------------------------------------------|-------|-------|
| `plain` | 无压缩，直接复制                                                                                              | ★★★★★ | ☆     |
| `gzip`  | 基于 [zlib](https://www.zlib.net/) 的 [gzip](https://docs.python.org/3/library/gzip.html) 库。`.gz` 文件同款格式 | ★★    | ★★★★  |
| `lzma`  | [LZMA](https://docs.python.org/3/library/lzma.html) 算法。`.xz` 文件同款格式。提供最佳的压缩率，但是速度非常慢                  | ☆     | ★★★★★ |
| `zstd`  | [Zstandard](https://github.com/facebook/zstd) 算法。一个优秀的压缩算法，在速度和压缩率间取得了较好的平衡。推荐使用                      | ★★★☆  | ★★★★  |
| `lz4`   | [LZ4](https://github.com/lz4/lz4) 算法。比 Zstandard 快，解压速度非常快，但是压缩率相对较低                                  | ★★★★  | ★★☆   |

!!! warning

    更改 `compress_method` 只会影响新备份中的新文件（即新的数据对象）

!!! note

    如果你想使用 `lz4` 作为压缩方法，你需要手动安装 `lz4` python 库

    ```bash
    pip3 install lz4
    ```

- 类型：`str`
- 默认值：`"zstd"`

#### compress_threshold

对于大小小于 `compress_threshold` 的文件，不弃用压缩。它们将以 `plain` 格式存储

!!! warning

    更改 `compress_threshold` 只会影响新备份中的新文件（即新的数据对象）

- 类型：int
- 默认值：`64`

---

### 定时备份配置

定时备份功能的配置

该功能会定期为服务器自动创建备份

```json
{
    "enabled": false,
    "interval": "12h",
    "crontab": null,
    "jitter": "10s",
    "reset_timer_on_backup": true,
    "require_online_players": false
}
```

#### enabled, interval, crontab, jitter

见 [定时作业配置](#定时作业配置) 小节

#### reset_timer_on_backup

是否在每次手动备份时重置计划定时器

- 类型：`bool`
- 默认值：`true`

#### require_online_players

若设为 `true`，则只有在服务器中存在玩家时，才进行定时备份

注意：该功能需要 Prime Backup 插件在服务器启动前就被加载。
若 Prime Backup 插件在服务器运行过程中被加载，定时备份功能将被禁用，
除非插件 [MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI) 存在

由于 Prime Backup 支持文件去重以及高可自定义的 [剪裁配置](#剪裁配置) 功能，
因此就算服务器里没人也备份，也不会导致备份占用过多空间

- 类型：`bool`
- 默认值：`false`

---

### 剪裁配置

Prime Backup 的备份剪裁功能可用于自动清理过时备份

```json
{
    "enabled": true,
    "interval": "3h",
    "crontab": null,
    "jitter": "20s",
    "timezone_override": null,
    "regular_backup": {
        "enabled": false,
        "max_amount": 0,
        "max_lifetime": "0s",
        "last": -1,
        "hour": 0,
        "day": 0,
        "week": 0,
        "month": 0,
        "year": 0
    },
    "pre_restore_backup": {
        "enabled": true,
        "max_amount": 10,
        "max_lifetime": "30d",
        "last": -1,
        "hour": 0,
        "day": 0,
        "week": 0,
        "month": 0,
        "year": 0
    }
}
```

它包含两种剪裁设置，分别针对于如下两种类型的备份：

- `regular_backup`: 针对常规备份，即非回档前备份
- `pre_restore_backup`: 针对回档前备份

每种剪裁设置都详细描述了存档的保留策略

Prime Backup 会执行以下步骤来决定删除/保留哪些备份

1. 使用 [`last`, `hour`, `day`, `week`, `month`, `year`](#last-hour-day-week-month-year) 筛选出要删除/保留的备份
2. 使用 `max_amount`、`max_lifetime`，在第 1 步保留的那些备份中，筛选出那些旧的和过期的备份
3. 收集上面 2 步中筛出来的那些需要删除的备份，逐个进行删除

#### max_amount

定义要保留的最大备份数量，例如 `10` 表示最多保留最新的 10 个备份

设置为 `0` 表示无限制

- 类型：`int`

#### max_lifetime

定义所有备份的最大保存时长。超出给定时长的备份将被裁剪删除

设置为 `0s` 表示无时长限制

- 类型：[`Duration`](#duration)

#### last, hour, day, week, month, year

一组 [PBS](https://pbs.proxmox.com/) 风格的剪裁选项，用于描述备份的删除/保留方式

查看 [剪裁模拟器](https://pbs.proxmox.com/docs/prune-simulator/) 了解这些选项的更多解释

[剪裁模拟器](https://pbs.proxmox.com/docs/prune-simulator/) 也可用于模拟备份的保留策略

注意：值 `0` 表示不为该区间保留任何备份；值 `-1` 表示该区间可以保留无限多的备份，与设为极大值等价

- 类型：`int`

---

#### enabled, interval, crontab, jitter

见 [定时作业配置](#定时作业配置) 小节

#### timezone_override

在裁剪期间，所使用的时区。默认情况下（使用 `null` 值），Prime Backup 将使用本地时区

例子：`null`, `"Asia/Shanghai"`, `"US/Eastern"`, `"Europe/Amsterdam"`

- 类型：`Optional[str]`
- 默认值：`null`

---

### 数据库配置

Prime Backup 所使用的 SQLite 数据库的相关配置

```json
{
    "compact": {
        "enabled": true,
        "interval": "1d",
        "crontab": null,
        "jitter": "5m"
    },
    "backup": {
        "enabled": true,
        "interval": "7d",
        "crontab": null,
        "jitter": "10m"
    }
}
```

子配置 `compact` 和 `backup` 描述了与数据库相关的定时作业

#### compact

数据库精简作业

它对数据库使用了 [VACUUM](https://www.sqlite.org/lang_vacuum.html)指令， 以精简数据库文件，并释放未使用的空间

#### backup

数据库备份作业

默认情况下，Prime Backup 会定期在 [数据根目录](#storage_root) 内的 
`db_backup` 目录中创建数据库备份，以防数据库文件损坏而导致无法访问备份

数据库备份将以 `.tar.xz` 格式存储，不会占用太多空间

#### enabled, interval, crontab, jitter

见 [定时作业配置](#定时作业配置) 小节

--- 

## 子配置项说明

### 定时作业配置

一个定时作业相关的配置，用于描述该作业会在什么时候执行。有两种模式：

- 间隔模式：按给定的时间间隔执行作业。第一次执行也要等待给定的间隔
- 定时模式: 在特定时间执行作业，由 crontab 字符串描述

若作业被启用，你必须选择上述模式之一，并正确设置相关配置值

```json
// 例子
{
    "enabled": true,
    "interval": "1h",
    "crontab": null,
    "jitter": "10s"
}
```

#### enabled

作业的开关。设为 `true` 以启用该作业，设为 `false` 以禁用该定时作业

- 类型：`bool`

#### interval

在间隔模式中使用。两次任务之间的时间间隔

若作业未使用间隔模式，其值应为 `null`

- 类型：`Optional[str]`

#### crontab

在定时模式中使用。描述定时计划的一个 crontab 字符串

你可以使用 [https://crontab.guru/](https://crontab.guru/) 来创建一个 crontab 字符串

若作业未使用定时模式，其值应为 `null`

- 类型：`Optional[str]`

#### jitter

两次作业之间，执行之间的抖动

下一个任务的实际执行时间，将在范围 `[-jitter, +jitter]` 内进行随机偏移

设置为 `"0s"` 表示无抖动

- 类型：`str`

---

## 特殊的值类型

### Duration

使用字符串描述的时间持续长度，如：`"3s"`、`"15m"`

Duration 由两部分组成：数字和时间单位。

对于数字部分，它可以是整数或浮点数

对于单位部分，参见下表：

| 单位             | 描述 | 等价于     | 秒数       |
|----------------|----|---------|----------|
| `ms`           | 毫秒 | 0.001 秒 | 0.001    |
| `s`, `sec`     | 秒  | 1 秒     | 1        |
| `m`, `min`     | 分钟 | 60 秒    | 60       |
| `h`, `hour`    | 小时 | 60 分钟   | 3600     |
| `d`, `day`     | 天  | 24 小时   | 86400    |
| `mon`, `month` | 月  | 30 天    | 2592000  |
| `y`, `year`    | 年  | 365 天   | 31536000 |
