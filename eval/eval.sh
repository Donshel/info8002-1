START=5
STEP=5
END=35

LOOK=100

DIR='products/txt'

rm -rf $DIR

for ((i=$START;i<=$END;i+=STEP))
do
    mkdir -p $DIR/$i

    (../bash/boot.sh $i) 2> $DIR/$i/boot.txt
    ../bash/ping.sh $i

    for ((j=0;j<$LOOK;j++))
    do
        port=$((5000 + $RANDOM % $i))
        key=$(($RANDOM % 2**10))
        curl http://127.0.0.1:$port/lookup/$key >> $DIR/$i/lookup.txt
        curl http://127.0.0.1:$port/network >> $DIR/$i/network.txt
    done

    ../bash/shut.sh $i
done
