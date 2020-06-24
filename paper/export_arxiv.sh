#!/bin/bash

if [[ $(git diff --shortstat 2> /dev/null | tail -n1) != "" ]] ; then
  echo "Cant export - would possibly override stuff"
  exit 0
fi

sed -i '/^%/ d' tdcch.tex
sed -i 's/bibliography{references_nocrossrefs}/input{tdcch.bbl}/' tdcch.tex

zip arxiv.zip \
tdcch.tex \
orcid.pdf \
tdcch.bbl \
lipics-v2019.cls \
fig/* \
table/related_work.tex \
table/search_space_stats.tex \

git checkout tdcch.tex
