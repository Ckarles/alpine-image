#!/usr/bin/env bash

set -e

[ -z "${FETCH_URL}" ] && exit 2
ROOTFS="${FETCH_URL##*/}"

mkdir -v /mnt/alpine && cd "${_}"

# download alpine
curl -so "${ROOTFS}" "${FETCH_URL}"
curl -so "${ROOTFS}.sha512" "${FETCH_URL}.sha512"
sha512sum -c "${ROOTFS}.sha512"

# unpack rootfs
tar -xzf "${ROOTFS}"

# prepare chroot
cp -v --dereference /etc/resolv.conf etc/resolv.conf
mount -v -t proc proc proc
mount -v --rbind /dev dev
mount -v --make-rslave dev
mount -v --rbind /sys sys
mount -v --make-rslave sys
mount -v --rbind /tmp tmp

# add chroot to next ssh connection
usermod -s /bin/sh root
echo "ChrootDirectory /mnt/alpine" | tee -a /etc/ssh/sshd_config
systemctl reload sshd

chroot . /bin/sh <<- EOF
  apk add \
    alpine-conf         `#setup-alpine utilities` \
    openssh             `#scp chroot bin` \
    openssh-sftp-server `#sftp-server chroot bin`
EOF

# kill all ssh connections to prepare for the chroot
nohup bash <<- EOF
  systemctl stop sshd
  pkill -9 ssh
  systemctl start sshd
EOF
