#!/bin/bash

if [[ $(git diff --shortstat 2> /dev/null | tail -n1) != "" ]] ; then
  echo "Cant export - would possibly override stuff"
  exit 0
fi

sed -i '/^%/ d' tdcch.tex

zip dagstuhl.zip \
tdcch.tex \
references.bib \
lipics-v2019.cls \
fig/* \
table/related_work.tex \
table/search_space_stats.tex \

git checkout tdcch.tex
