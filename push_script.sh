#!/bin/bash
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_rsa
git push -u origin master
