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
    curl http://127.0.0.1:$i/shutdown
done
