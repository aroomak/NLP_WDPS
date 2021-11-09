#!/bin/sh
#!/bin/sh

echo "Processing webpages ..."
python3 Run_Gp33_Final.py input_warc_files > Result_predictions.tsv
echo "Computing the scores ..."
python3 score.py input_sample_annotations Result_predictions.tsv

#echo "Computing the scores ..."
#python3 score.py Answer_annotations.tsv Result_predictions.tsv
