# CATCHUp

*Customizable Approximated Time-dependent Contraction Hierarchies through UnPacking*

---

This repository contains the source code for the paper, the experiments and the evaluation of the ESA2020 paper "Space-efficient, Fast and Exact Routing in Time-dependent Road Networks".
Everything is tied together using `rake`.
Experiments can be run with `rake exp:all`.
The default `rake` tasks builds the paper.
This step also uses the output of the experiments to rebuild figures used in the paper.
The algorithmic code can be found in the `code` directory where several projects are included as submodules.
The code for CATCHUp actually lives in https://github.com/kit-algo/rust_road_router .
For reproducibility, this repository references the exact version used to perform the experiments for the paper.
However, if you want to read the code you should probably just use the current master branch as the repository has been restructured, cleaned up and documented since then.
