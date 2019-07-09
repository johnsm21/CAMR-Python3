#CORENLP_PATH='/home/j/llc/cwang24/Tools/CoreNLP-mod-convert.jar'
#CORENLP_PATH='/home/j/llc/cwang24/Tools/CoreNLP-mod-convert-collapse.jar'
CORENLP_PATH=$2
java -Xmx1800m -cp $CORENLP_PATH/CoreNLP-mod-convert-collapse.jar edu.stanford.nlp.trees.EnglishGrammaticalStructure -basic -treeFile $1 > $1.dep
