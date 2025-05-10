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


## Future Modifications

The reason for using Cloudinary is the fact that their services are free up to 25GB, which is huge. If there is need for higher storage (which may arise someday), more backup classes would be written to support the requirement for paid storage vendors. But that's an enhancement for some other time.
