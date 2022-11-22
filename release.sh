#!/bin/bash

FULL_NAME=`date "+%Y%m%d%H"`
VERSION_0=`echo $FULL_NAME | cut -c 2-4`
VERSION_1=`echo $FULL_NAME | cut -c 5-7`
VERSION_2=`echo $FULL_NAME | cut -c 8-10`
VERSION=$VERSION_0.$VERSION_1.$VERSION_2

CURRENT_BRANCH=`git branch --show-current`
GIT_HASH=`git log -1 --format=%H`
RELEASED_BY=`whoami`

echo "VERSION = \"$VERSION-$GIT_HASH\"" > version.py
echo "RELEASED_BY = \"$RELEASED_BY\"" >> version.py
git add version.py
git commit -m "released by $RELEASED_BY"

git checkout -b release/$VERSION
git push --set-upstream origin release/$VERSION
git checkout $CURRENT_BRANCH
