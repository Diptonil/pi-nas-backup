# PiNAS Cloud Backups

*Codename: BatBackup*

This is a *highly lightweight CLI utility for manual cloud (Cloudinary) backups of compressed and optionally encrypted local data, ideally for a RaspberryPi*. The compression is default (not optional) while encyption is optional. The utility supports only Cloudinary. It serves both backup and restore operations.


## Who is This Not For?

Please note that there are way better solutions (for most homelabbers) available for this. <a href="https://rclone.org/">RClone</a> is one of the best. For enterprise solutions (or even personal use-cases where the scale of data being dealt with is too large and critical), RClone (or something like <a href="https://github.com/duplicati/duplicati">Duplicati</a>) would be the way to go.

The goal for doing this was because I needed a one-off manual solution that *lives outside Docker, utilizes less resources, and suits my very specific needs of selective backups and compression.


## Who is this For?

Primarily for users with a low to moderate scale of data queued for a backup to Cloudinary. The solution was built to *manually back up selective files on a custom-built Pi5 NAS to the cloud after encryption & compression*.
This solution does not intend to boast a UI, scheduled sync-ups, incremental snapshotting, vendor support, etc. The extension can be very well made, but the whole point of this is to avoid any complexity at all.

**No containers, no daemons. Just one command and you're done after a few minutes. This is a highly specific and customized utility that may not work for most users.** Even then, parts of the code may be reused.

That said, this script can be scheduled with the use of a cron job on a Pi with ease, if required.


## Logic

Given the highly specific requirements of the project, here is how backups are implemented:
- A `location.txt` file is read from. It contains a list of locations that would need to be backed up, along with the category the data belongs to. This is changed everytime a manual backup is initiated.
- The `summary.csv` file is read from. It is a log of all directories backed up over time, along with the timestamp of the backup and original size. If any location found in `summary.csv` is repeated in `location.txt`, the cloud object is deleted (basically, if a cloud backup of a resource already exists that needs to be backed up again, the latest version would backed up and the previous data would get overwritten).
- The data to back up is collected, GZIPped and encrypted (if -e flag is present).
- The data is sent over to the Cloud.
- The `summary.csv` is appended to. If anything is re-written, the new entry comes up now.

The inverse operation is used for the unpacker (backup-retrieval) class.


## Environment Secrets

The program is designed to read from a `.env` file. The file should have these parameters to work:

```
CLOUD_NAME=
API_KEY=
API_SECRET=
PASSWORD=
```

- The first three variables are specific to Cloudinary.
- The `PASSWORD` is basically the key used to encrypt and decrypt data.
- A demo file `.env.demo` is available in this repository for reference.


## Usage: To Back Up

- Specify the locations for the files or folders to be backed up in `reports/locations.txt`. For example:

```
/home/user/Videos/Screencasts/hi.log
/home/user/Videos/Screencasts/Screencast from 22-10-24 12:28:17 PM IST.webm
/home/user/Videos/Screencasts/Screencast from 22-10-24 12:52:35 PM IST.webm
/home/user/Videos/Screencasts

```

- To start the backup process:

```sh
# Without encryption
python3 main.py

# With encryption
python3 main.py -e
```

- Validate the status using console logs or file logs stored in `logs/{date}.log`.
- Check the `reports/summary.csv` file. That keeps a track of all backups made using this utility, providing a view of the current state of backups (the files, space used and the date they were last changed).


## Usage: To Retrieve

This retrieves the entire cloud backup, decrypts any file needing decryption. No exceptions.

- To start retrieval:

```sh
python3 main.py -r
```
- Validate the status using console logs or file logs stored in `logs/{date}.log`.
- The files get stored in `backups` directory.


## Benchmarking

The application was benchmarked on a system with the following following stats:

```
2025-05-16 13:39:59,982 | INFO | OS: Linux
2025-05-16 13:39:59,983 | INFO | OS Version: #61~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue Apr 15 17:03:15 UTC 2
2025-05-16 13:39:59,983 | INFO | Platform: Linux-6.8.0-59-generic-x86_64-with-glibc2.35
2025-05-16 13:39:59,983 | INFO | Architcture: x86_64
2025-05-16 13:39:59,983 | INFO | Processor: x86_64
2025-05-16 13:39:59,984 | INFO | Total Memory (GB): 8.217972736
2025-05-16 13:39:59,984 | INFO | Disk (GB): 298.650124288
```

The results for backup creation for one folder of 2 MB and 3 files of less than a few MBs:

```
2025-05-16 13:39:59,984 | INFO | Execution Time (minutes): 0.2712160031000773
2025-05-16 13:39:59,984 | INFO | CPU (User) Time (minutes): 0.0405
2025-05-16 13:39:59,985 | INFO | CPU (System) Time (minutes): 0.0018333333333333335
2025-05-16 13:39:59,985 | INFO | Virtual Memory (MB): 73.76953125
2025-05-16 13:39:59,985 | INFO | Resident Set Memory (MB): 43.85546875
2025-05-16 13:39:59,985 | INFO | I/O Read (MB): 0.0
2025-05-16 13:39:59,985 | INFO | I/O Write (MB): 7.2578125
```

The benchmarking scenario deals with way too small inputs and is far from ideal. Suprisingly, I didn't have much larger files on my local system to validate them. The point here is to state that a benchmarking utility is readily available, although the reports here are largely irrelevant given their far-from-usual inputs. To start benchmark:

```sh
python3 benchmark.py
```

The benchmark is run on whatever is present in `reports/locations.txt`.


## Future Modifications

The reason for using Cloudinary is the fact that their services are free up to 25GB, which is huge. If there is need for higher storage (which may arise someday), more backup classes would be written to support the requirement for paid storage vendors. But that's an enhancement for some other time.
