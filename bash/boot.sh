if [ -z "$1" ]
then
    n=10
else
    n=$1
fi

START=5000
END=$(($START + $n))

for ((i=$START;i<$END;i++))
do
    python ../python/application.py -p $i &
done
