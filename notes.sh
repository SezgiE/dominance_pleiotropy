scp -r /Users/sezgi/Documents/dominance_heritability/ref_genome sercan@snellius.surf.nl:/home/sercan/dominance/dominance_pleiotropy


sbatch submit_pipeline.sbatch
tail -f pipeline_ID.out

squeue -j <JOBID>
sacct -j <JOBID> --format=JobID,JobName,Elapsed,State