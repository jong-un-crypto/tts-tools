#!/bin/bash
while true; do
  rclone sync /asset unc_cf:asset/asset/ --log-file=sync.log --log-level=INFO
  sleep 1
done
