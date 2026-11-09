#!/usr/bin/env bash
# Wipe My Assist's data and rebuild it purely by replaying Kafka from the beginning.
set -euo pipefail
cd "$(dirname "$0")/.."
DC="docker compose"
GROUP=replica-consumer
TOPIC=task-events
KT=/opt/kafka/bin

echo "==> stopping replica-consumer"
$DC stop replica-consumer

echo "==> truncating tasks_replica and task_activity in DB-B"
$DC exec -T db-b sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "TRUNCATE tasks_replica, task_activity"'

echo "==> resetting consumer group '$GROUP' to earliest offsets"
$DC exec -T kafka $KT/kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group $GROUP --topic $TOPIC --reset-offsets --to-earliest --execute

echo "==> restarting replica-consumer (replaying $TOPIC from the start)"
$DC start replica-consumer

echo "==> waiting for the consumer to catch up"
for i in $(seq 1 120); do
  LAG=$($DC exec -T kafka $KT/kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
        --group $GROUP --describe 2>/dev/null | awk -v t=$TOPIC '$2==t && $6 ~ /^[0-9]+$/ {s+=$6; n++} END {if (n>0) print s; else print "x"}')
  if [ "$LAG" = "0" ]; then echo "    caught up (lag 0)"; break; fi
  [ "$i" = 120 ] && { echo "timed out waiting for catch-up (lag=$LAG)"; exit 1; }
  sleep 2
done
sleep 1

echo "==> comparing Smart Admin and My Assist"
$DC --profile tools run --rm -T tools python scripts/compare_systems.py
