# Expand hardware substitution file to an output file.
# Args: SUBST TEMP FILE
SUBST=$1
TEMP=$2
FILE=$3
msi -S $1 > $2$3  
