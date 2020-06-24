raise "No or wrong graph data dir configured - please set TDCCH_GRAPH_DIR env var" unless Dir.exists? ENV['TDCCH_GRAPH_DIR'] || ""
raise "No or wrong main graph configured - please set TDCCH_MAIN_GRAPH env var" unless Dir.exists? "#{ENV['TDCCH_GRAPH_DIR']}/#{ENV['TDCCH_MAIN_GRAPH']}"
raise "No or wrong experiments output dir configured - please set TDCCH_EXP_OUTPUT_DIR env var" unless Dir.exists? ENV['TDCCH_EXP_OUTPUT_DIR'] || ""

file "paper/tdcch.pdf" => [
  "paper/tdcch.tex",
  "paper/table/approx_params_running_times.tex",
  "paper/table/approx_params_active_ipps_avg.tex",
  "paper/table/search_space_stats.tex",
  "paper/table/related_work.tex",
  "paper/fig/ranks.pdf",
  "paper/fig/customization_scaling.pdf",] do

  Dir.chdir "paper" do
    sh "latexmk -pdf tdcch.tex"
  end
end

task default: "paper/tdcch.pdf"

namespace "fig" do
  file "paper/fig/ranks.pdf" => FileList["#{ENV['TDCCH_EXP_OUTPUT_DIR']}/rank_queries_all_graphs/*.json"] + FileList["#{ENV['TDCCH_EXP_OUTPUT_DIR']}/rank_query_stats_no_astar_all_graphs/*.json"] + ['eval/rank_plot.py'] do
    sh "eval/rank_plot.py"
  end

  file "paper/fig/customization_scaling.pdf" => FileList["#{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_scaling/*.json"] + ['eval/customization_scaling.py'] do
    sh "eval/customization_scaling.py"
  end
end

namespace "table" do
  file "paper/table/approx_params_active_ipps_avg.tex" => FileList["#{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_approx/*.json"] + ["eval/approx_params.py"] do
    sh "eval/approx_params.py"
  end
  file "paper/table/approx_params_running_times.tex" => FileList["#{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_approx/*.json"] + ["eval/approx_params.py"] do
    sh "eval/approx_params.py"
  end

  file "paper/table/search_space_stats.tex" => FileList["#{ENV['TDCCH_EXP_OUTPUT_DIR']}/query_stats_all_graphs/*.json", "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/query_stats_no_astar_all_graphs/*.json"] + ["eval/search_space_stats.py"] do
    sh "eval/search_space_stats.py"
  end

  file "paper/table/related_work.tex" => FileList[
    "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/katch/contraction/*.out",
    "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/katch/uniform_queries/*.out",
    "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/tds/contraction/*.out",
    "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/tds/uniform_queries/*.out",
    "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/queries_all_graphs/*.json",
    "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_all_graphs/*.json",
    "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/partition/*.out",
    "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/contraction/*.json",
    ] + ["eval/related_work_cmp.py"] do

    sh "eval/related_work_cmp.py"
  end
end

tds_windows = [[0, 240], [350, 370], [410, 430], [470, 490], [600, 720], [720, 840], [960, 1020], [1020, 1080], [1140, 1260]]

namespace "exp" do
  desc "Run all experiments"
  task all: [:partition, :contraction, :customization_opt, :customization_approx, :customization_scaling, :customization, :query]

  directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/partition"
  directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/contraction"
  directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_all_graphs"
  directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_optimizations"
  directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_approx"
  directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_scaling"
  directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/queries_all_graphs"
  directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/rank_queries_all_graphs"
  directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/query_stats_all_graphs"
  directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/rank_query_stats_all_graphs"
  directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/query_stats_no_astar_all_graphs"
  directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/rank_query_stats_no_astar_all_graphs"

  desc "Run main contraction experiments"
  task partition: ["code/rust_road_router/lib/FlowCutter-Accelerated/release/console", "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/partition"] do
    Dir.chdir "code/rust_road_router" do
      Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/").each do |graph|
        5.times do
          filename = "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/partition/" + `date --iso-8601=seconds`.strip + '.out'
          sh "echo '#{graph}' >> #{filename}"
          sh "./flow_cutter_cch_order.sh #{graph} #{Etc.nprocessors} >> #{filename}"
        end
      end
    end
  end

  desc "Run main contraction experiments"
  task contraction: FileList["#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/"].map { |g| g + "/cch_perm" } + ["#{ENV['TDCCH_EXP_OUTPUT_DIR']}/contraction"] do
    Dir.chdir "code/rust_road_router/engine" do
      Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/").each do |graph|
        5.times do
          sh "cargo run --release --bin tdcch_static_preprocessing -- #{graph} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/contraction/$(date --iso-8601=seconds).json"
        end
      end
    end
  end

  desc "Run main customization experiments"
  task customization: FileList["#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/"].map { |g| g + "/cch" } + ["#{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_all_graphs"] do
    Dir.chdir "code/rust_road_router/engine" do
      Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/").each do |graph|
        5.times do
          sh "cargo run --release --bin tdcch_customization -- #{graph} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_all_graphs/$(date --iso-8601=seconds).json"
        end
      end
    end
  end

  desc "Run customization experiments without certain optimizations"
  task customization_opt: FileList["#{ENV['TDCCH_GRAPH_DIR']}/#{ENV['TDCCH_MAIN_GRAPH']}/cch", "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_optimizations"] do
    Dir.chdir "code/rust_road_router/engine" do
      sh "cargo run --release --no-default-features --features 'report-to-stderr tdcch-approx tdcch-postcustomization tdcch-triangle-sorting' --bin tdcch_customization -- #{ENV['TDCCH_GRAPH_DIR']}/#{ENV['TDCCH_MAIN_GRAPH']} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_optimizations/$(date --iso-8601=seconds).json"
      sh "cargo run --release --no-default-features --features 'report-to-stderr tdcch-approx tdcch-precustomization tdcch-postcustomization' --bin tdcch_customization -- #{ENV['TDCCH_GRAPH_DIR']}/#{ENV['TDCCH_MAIN_GRAPH']} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_optimizations/$(date --iso-8601=seconds).json"
    end
    sh "rm -r #{ENV['TDCCH_GRAPH_DIR']}/#{ENV['TDCCH_MAIN_GRAPH']}/customized"
  end

  desc "Run customization approx params experiments"
  task customization_approx: FileList["#{ENV['TDCCH_GRAPH_DIR']}/#{ENV['TDCCH_MAIN_GRAPH']}/cch", "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_approx"] do
    Dir.chdir "code/rust_road_router/engine" do
      [0.1, 0.5, 1.0, 5.0, 10.0].each do |epsilon|
        [100, 500, 1000, 5000, 10000].each do |threshold|
          begin
            sh "TDCCH_APPROX=#{epsilon} TDCCH_APPROX_THRESHOLD=#{threshold} cargo run --release --features 'detailed-stats' --bin tdcch_customization -- #{ENV['TDCCH_GRAPH_DIR']}/#{ENV['TDCCH_MAIN_GRAPH']} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_approx/$(date --iso-8601=seconds).json"
          rescue Exception => e
            puts "approx run crashed", e
          end
        end
      end
    end
    sh "rm -r #{ENV['TDCCH_GRAPH_DIR']}/#{ENV['TDCCH_MAIN_GRAPH']}/customized"
  end

  desc "Run customization scaling experiments"
  task customization_scaling: FileList["#{ENV['TDCCH_GRAPH_DIR']}/#{ENV['TDCCH_MAIN_GRAPH']}/cch", "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_scaling"] do
    Dir.chdir "code/rust_road_router/engine" do
      5.times do
        sh "cargo run --release --features tdcch-disable-par --bin tdcch_customization -- #{ENV['TDCCH_GRAPH_DIR']}/#{ENV['TDCCH_MAIN_GRAPH']} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_scaling/$(date --iso-8601=seconds).json"
      end

      num_threads = 1
      while num_threads <= Etc.nprocessors
        5.times do
          sh "RAYON_NUM_THREADS=#{num_threads} cargo run --release --bin tdcch_customization -- #{ENV['TDCCH_GRAPH_DIR']}/#{ENV['TDCCH_MAIN_GRAPH']} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/customization_scaling/$(date --iso-8601=seconds).json"
        end
        num_threads *= 2
      end
    end
  end

  desc "Run main query experiments"
  task query: FileList["#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/"].map { |g| g + "/customized" } + [
      "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/queries_all_graphs",
      "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/rank_queries_all_graphs",
      "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/query_stats_all_graphs",
      "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/rank_query_stats_all_graphs",
      "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/query_stats_no_astar_all_graphs",
      "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/rank_query_stats_no_astar_all_graphs"] do
    Dir.chdir "code/rust_road_router/engine" do
      sh "cargo clean"
      Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/").each do |graph|
        sh "RUSTFLAGS='-C target-cpu=native' cargo run --release --bin tdcch_pregen_uniform_queries -- #{graph} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/queries_all_graphs/$(date --iso-8601=seconds).json"
        sh "RUSTFLAGS='-C target-cpu=native' cargo run --release --bin tdcch_pregen_rank_queries -- #{graph} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/rank_queries_all_graphs/$(date --iso-8601=seconds).json"
        sh "RUSTFLAGS='-C target-cpu=native' cargo run --release --features 'detailed-stats' --bin tdcch_pregen_uniform_queries -- #{graph} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/query_stats_all_graphs/$(date --iso-8601=seconds).json"
        sh "RUSTFLAGS='-C target-cpu=native' cargo run --release --features 'detailed-stats' --bin tdcch_pregen_rank_queries -- #{graph} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/rank_query_stats_all_graphs/$(date --iso-8601=seconds).json"
        sh "RUSTFLAGS='-C target-cpu=native' cargo run --release --no-default-features --features 'detailed-stats' --bin tdcch_pregen_uniform_queries -- #{graph} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/query_stats_no_astar_all_graphs/$(date --iso-8601=seconds).json"
        sh "RUSTFLAGS='-C target-cpu=native' cargo run --release --no-default-features --features 'detailed-stats' --bin tdcch_pregen_rank_queries -- #{graph} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/rank_query_stats_no_astar_all_graphs/$(date --iso-8601=seconds).json"
      end
      sh "cargo clean"
    end
  end

  namespace "alt" do
    namespace "katch" do
      directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/katch/contraction"
      directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/katch/uniform_queries"
      directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/katch/rank_queries"

      desc "Run KaTCH contraction experiments"
      task contraction: FileList["#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/"].map { |g| g + "/graph.tpgr" } + FileList["#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/"].map { |g| g + "/katch" } + ["code/KaTCH/examples/run_ordering", "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/katch/contraction"] do
        Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/").each do |graph|
          sh "code/KaTCH/examples/run_ordering #{graph}/graph.tpgr #{graph}/katch/hierarchy.tch #{Etc.nprocessors} > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/katch/contraction/$(date --iso-8601=seconds).out"
        end
      end

      ["uniform", "rank"].each do |query_type|
        desc "Run KaTCH #{query_type} query experiments"
        task "#{query_type}_queries" => FileList["#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/"].map { |g| g + "/katch/hierarchy.tch" } +
            FileList["#{ENV['TDCCH_GRAPH_DIR']}/*/#{query_type}_queries/day/*/"].map { |g| g + "/queries.demands" } +
            ["code/KaTCH/examples/run_tch_ea_query", "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/katch/#{query_type}_queries"] do
          Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/").each do |graph|
            begin
              sh "code/KaTCH/examples/run_tch_ea_query #{graph}/katch/hierarchy.tch #{graph}/../../#{query_type}_queries/day/#{File.basename graph}/queries.demands > #{ENV['TDCCH_EXP_OUTPUT_DIR']}/katch/#{query_type}_queries/$(date --iso-8601=seconds).out"
            rescue Exception => e
              puts "KaTCH queries crashed", e
            end
          end
        end
      end

      desc "All KaTCH query experiments"
      task queries: [:uniform_queries, :rank_queries]
    end

    namespace "tds" do
      directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/tds/contraction"
      directory "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/tds/uniform_queries"

      desc "TD-S CH computation"
      task contraction: FileList["#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/"].map { |g| g + "/tds/win9" } + ["code/RoutingKit/lib", "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/tds/contraction"] do
        Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/").each do |graph|
          `mkdir -p #{graph}/tds/ch9`
          filename = "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/tds/contraction/" + `date --iso-8601=seconds`.strip + '.out'
          sh "echo '#{graph}' >> #{filename}"
          tds_windows.each do |window_start, window_end|
            sh "code/RoutingKit/bin/compute_contraction_hierarchy #{graph}/{first_out,head} #{graph}/tds/win9/#{window_start}_#{window_end} #{graph}/tds/ch9/#{window_start}_#{window_end} >> #{filename}"
          end
        end
      end

      desc "Run TD-S uniform query experiments"
      task "uniform_queries" => FileList["#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/"].map { |g| g + "/tds/ch9" } +
          ["code/td_p/bin", "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/tds/uniform_queries"] do
        Dir.chdir "code/rust_road_router/engine" do
          Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/").each do |graph|
            filename = "#{ENV['TDCCH_EXP_OUTPUT_DIR']}/tds/uniform_queries/" + `date --iso-8601=seconds`.strip + '.out'
            sh "echo '#{graph}' >> #{filename}"
            sh "cargo run --release --bin td_ben_queries_to_stdout -- #{graph}/../../uniform_queries/ | head -n10000 | ../../td_p/bin/run_td_s #{graph}/{first_out,head,first_ipp_of_arc,ipp_departure_time,ipp_travel_time} #{graph}/tds/ch9/* >> #{filename}"
          end
        end
      end
    end
  end

end

namespace "preprocessing" do
  Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/").each do |graph|
    desc "Calculating a nested dissection order with FlowCutter"
    file "#{graph}/cch_perm" => "code/rust_road_router/lib/FlowCutter-Accelerated/release/console" do
      Dir.chdir "code/rust_road_router" do
        sh "./flow_cutter_cch_order.sh #{graph} #{Etc.nprocessors}"
      end
    end

    desc "Metric independent CCH Preprocessing"
    file "#{graph}/cch" => "#{graph}/cch_perm" do
      Dir.chdir "code/rust_road_router/engine" do
        sh "cargo run --release --bin tdcch_static_preprocessing -- #{graph}"
      end
    end

    desc "Customization"
    file "#{graph}/customized" => "#{graph}/cch" do
      Dir.chdir "code/rust_road_router/engine" do
        sh "cargo run --release --bin tdcch_customization -- #{graph} > /dev/null"
      end
    end
  end

  namespace "alt" do
    desc "Generate all tpgr graphs"
    task all_tpgrs: FileList["#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/"].map { |g| g + "/graph.tpgr" }
    desc "Generate all tbgr graphs"
    task all_tbgrs: FileList["#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/"].map { |g| g + "/graph.tbgr" }

    Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/").each do |graph|
      desc "Generate graphs in tpgr format"
      file "#{graph}/graph.tpgr" do
        Dir.chdir "code/rust_road_router/engine" do
          sh "cargo run --release --bin td_ben_bin_to_veit_tpgr -- #{graph} #{graph}/graph.tpgr"
        end
      end

      desc "Generate graphs in tbgr format"
      file "#{graph}/graph.tbgr" do
        Dir.chdir "code/rust_road_router/engine" do
          sh "cargo run --release --bin td_ben_to_tbgr -- #{graph} #{graph}/graph.tbgr"
        end
      end
    end

    ["uniform", "rank"].each do |query_type|
      Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/#{query_type}_queries/day/*/").each do |graph|
        desc "Generate #{query_type} queries in demands format"
        file "#{graph}/queries.demands" do
          Dir.chdir "code/rust_road_router/engine" do
            sh "cargo run --release --bin td_ben_queries_to_veit_demands -- #{graph} #{graph}/queries.demands"
          end
        end
      end
    end

    namespace "katch" do
      Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/").each do |graph|
        directory "#{graph}/katch"

        desc "KaTCH Preprocessing"
        file "#{graph}/katch/hierarchy.tch" => ["#{graph}/katch", "#{graph}/graph.tpgr", "code/KaTCH/examples/run_ordering"] do
          sh "code/KaTCH/examples/run_ordering #{graph}/graph.tpgr #{graph}/katch/hierarchy.tch #{Etc.nprocessors}"
        end
      end
    end

    namespace :tds do
      Dir.glob("#{ENV['TDCCH_GRAPH_DIR']}/*/day/*/").each do |graph|
        directory "#{graph}/tds"
        directory "#{graph}/tds/win9"
        directory "#{graph}/tds/ch9"

        desc "TD-S window computation"
        file "#{graph}/tds/win9" => ["code/td_p/bin"] do
          tds_windows.each do |window_start, window_end|
            sh "code/td_p/bin/compute_time_window_weight #{window_start*60*1000} #{window_end*60*1000} #{graph}/{first_ipp_of_arc,ipp_departure_time,ipp_travel_time} #{graph}/tds/win9/#{window_start}_#{window_end}"
          end
        end

        desc "TD-S CH computation"
        file "#{graph}/tds/ch9" => ["#{graph}/tds/win9", "code/RoutingKit/lib"] do
          tds_windows.each do |window_start, window_end|
            sh "code/RoutingKit/bin/compute_contraction_hierarchy #{graph}/{first_out,head} #{graph}/tds/win9/#{window_start}_#{window_end} #{graph}/tds/ch9/#{window_start}_#{window_end}"
          end
        end
      end
    end
  end
end

namespace 'build' do
  task :flowcutter => "code/rust_road_router/lib/flow-cutter/console"

  desc "Building Flow Cutter"
  file "code/rust_road_router/lib/flow-cutter/console" do
    Dir.chdir "code/rust_road_router/lib/flow-cutter" do
      sh "./build.py --clean --ignore-warnings"
    end
  end

  directory "code/rust_road_router/lib/FlowCutter-Accelerated/release"

  task :inertialflowcutter => "code/rust_road_router/lib/FlowCutter-Accelerated/release/console"

  desc "Building Flow Cutter Accelerated"
  file "code/rust_road_router/lib/FlowCutter-Accelerated/release/console" => "code/rust_road_router/lib/FlowCutter-Accelerated/release" do
    Dir.chdir "code/rust_road_router/lib/FlowCutter-Accelerated/release" do
      sh "cmake -DCMAKE_BUILD_TYPE=Release .. && make console"
    end
  end

  task :katch => ["code/KaTCH/examples/run_ordering", "code/KaTCH/examples/run_tch_ea_query"]

  desc "Building KaTCH Preprocessing"
  file "code/KaTCH/examples/run_ordering" do
    Dir.chdir "code/KaTCH/examples" do
      sh "g++ -O3 -DNDEBUG -fopenmp -I.. -std=c++11 -o run_ordering run_ordering.cpp"
    end
  end

  desc "Building KaTCH Queries"
  file "code/KaTCH/examples/run_tch_ea_query" do
    Dir.chdir "code/KaTCH/examples" do
      sh "g++ -O3 -DNDEBUG -fopenmp -I.. -std=c++11 -o run_tch_ea_query run_tch_ea_query.cpp"
    end
  end

  task routingkit: "code/RoutingKit/lib"

  desc "Building RoutingKit Lib"
  file "code/RoutingKit/lib" do
    Dir.chdir "code/RoutingKit" do
      sh "make"
    end
  end

  task tds: "code/td_p/bin"

  desc "Build TD-S binaries"
  file "code/td_p/bin" => "code/RoutingKit/lib" do
    Dir.chdir "code/td_p" do
      sh "make CFLAGS='-I../RoutingKit/include -Wall -O3 -DNDEBUG -march=native -std=c++1y -fPIC -Iinclude' LDFLAGS='../RoutingKit/lib/libroutingkit.a'"
    end
  end
end

