r=1
n=""
while getopts 'r:n:' flag
do
    case "${flag}" in
        r) r=${OPTARG};;
        n) n=${OPTARG};;
    esac
done
python ./energy_sim.py $r $n