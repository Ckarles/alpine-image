#!/usr/bin/env bash

set -e

[ -z "${FETCH_URL}" ] && exit 2
ROOTFS_ARCHIVE="${FETCH_URL##*/}"

mkdir -v /mnt/alpine && cd "${_}"

# download alpine archive
curl -so "${ROOTFS_ARCHIVE}" "${FETCH_URL}"

# checksum archive
curl -so "${ROOTFS_ARCHIVE}.sha512" "${FETCH_URL}.sha512"
sha512sum -c "${ROOTFS_ARCHIVE}.sha512"
#rm "${ROOTFS_ARCHIVE}.sha512"

# unpack rootfs
tar -xzf "${ROOTFS_ARCHIVE}"
#rm "${ROOTFS_ARCHIVE}"

# prepare chroot
cp -v --dereference /etc/resolv.conf etc/resolv.conf
mount -v -t proc proc proc
mount -v --rbind /dev dev
mount -v --make-rslave dev
mount -v --rbind /sys sys
mount -v --make-rslave sys
mount -v --rbind /tmp tmp

# change root default shell to `sh`. bash is not available in alpine
usermod -s /bin/sh root

# setup host sshd to chroot in alpine
sed -i 's/^#\?\(ChrootDirectory\s*\)\S*$/\1\/mnt\/alpine/' \
	/etc/ssh/sshd_config

# change sftp subsystem to `/usr/lib/sftp-server` on host sshd config
sed -i 's/^\(Subsystem\s*sftp\s*\)\S*$/\1\/usr\/lib\/sftp-server/' \
	/etc/ssh/sshd_config

# add sftp-server to the same path in alpine
ln -s "/usr/lib/ssh/sftp-server" ./usr/lib/sftp-server

# install install requirements in alpine
chroot . /bin/sh <<- EOF
	apk add \
	  alpine-conf         `#setup-alpine utilities` \
	  openssh             `#scp chroot bin` \
	  openssh-sftp-server `#sftp-server chroot bin`
EOF

# restart ssh and kill all connections
# Necessary to ensure next ssh connection will be on chrooted alpine
#systemctl reload sshd
systemctl stop sshd
nohup bash <<- EOF
	pkill -9 ssh
	systemctl start sshd
EOF
