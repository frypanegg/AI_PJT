# home-core 사용 가이드

## 1. 준비

1. HA 프로필 → 보안 → **장기 액세스 토큰** 발급
2. `.env` 작성

```bash
cp .env.example .env
# HA_URL=http://192.168.219.xxx:8123
# HA_TOKEN=...
```

> 도커로 띄우면 `DB_PATH` 는 컨테이너 경로, 맥에서 직접 띄우면 로컬 파일이어야
> 한다. 도커용 주소를 그대로 두고 로컬 실행하면 연결이 실패한다.

3. 실행

```bash
pip install -r requirements.txt
uvicorn home_core.api:create_app --factory
```

`GET /health` 가 기기·방 개수를 돌려주면 붙은 것이다.

## 2. 기기 추가하기

`config/devices.yaml` 한 곳만 고치면 된다. 코드 수정은 필요 없다.

### 2-1. 일반 엔티티 (상태를 읽을 수 있는 기기)

```yaml
  living_room_stand:
    name: 거실 스탠드
    room: 거실
    kind: light
    capabilities:
      on_off:
        type: bool
        writable: true
        source: {entity_id: light.geosil_stand}
      brightness:
        type: number
        unit: "%"
        writable: true
        min: 0        # 우리 단위
        max: 100
        ha_min: 0     # HA 원본 단위
        ha_max: 255
        source: {entity_id: light.geosil_stand, attribute: brightness}
```

`min/max` 와 `ha_min/ha_max` 가 모두 있으면 어댑터가 선형 변환한다. 명령
`brightness=60` → HA 로는 `153` 이 나간다.

### 2-2. 씬 쌍 (Aqara E1 같은, 상태를 못 읽는 기기)

```yaml
  kitchen_light:
    name: 주방 조명
    room: 주방
    kind: light
    capabilities:
      on_off:
        type: bool
        writable: true
        source:
          members:                       # 한 기기가 흩어진 엔티티들
            "on": switch.jubang_kyeogi
            "off": switch.jubang_ggeugi
          command_targets:               # 명령 값 -> 실행할 엔티티
            "true": switch.jubang_kyeogi
            "false": switch.jubang_ggeugi
```

여기엔 **`entity_id` 가 없다.** 그래서 이 능력은 상태를 보고하지 않는다
(`readable: false`). 의도한 동작이다 — 씬 스위치의 `off` 를 조명 상태로 읽으면
"불이 켜져 있는데 꺼졌다고 답하는" LLM이 된다.

### 2-3. 전용 서비스가 필요한 경우

```yaml
      target_temperature:
        type: number
        writable: true
        min: 18
        max: 30
        service: climate.set_temperature    # turn_on 대신 이 서비스를 부른다
        source: {entity_id: climate.geosil_aircon, attribute: temperature}
```

## 3. 제어

```bash
curl -X POST localhost:8000/devices/kitchen_light/command \
     -H 'content-type: application/json' \
     -d '{"capability": "on_off", "value": false}'
```

응답의 `entity_id` 가 실제로 실행된 씬이다. **몇 번을 보내도 결과가 같다** —
자동화와 LLM이 믿고 쓸 수 있는 유일한 형태다.

## 4. 상태 구독 (SSE)

```bash
curl -N localhost:8000/events
# data: {"type":"state","device_id":"washer","capability":"status","value":"rinsing"}
# data: {"type":"command","device_id":"balcony_light","capability":"on_off","value":true,...}
```

값이 **변했을 때만** 발행된다. 폴링 주기는 `POLL_INTERVAL`(기본 10초).

## 5. 이력

```bash
curl 'localhost:8000/history?device_id=washer&limit=20'
```

값은 타입별 컬럼(`value_bool` / `value_num` / `value_text`)에 나뉘어 들어간다.
한 컬럼에 섞으면 `0` 과 `false` 가 구분되지 않는다.

## 6. LLM 붙일 때 주의할 것

- **상태를 못 읽는 조명이 있다.** `/devices` 의 `readable: false` 를 그대로
  전달해서, 모델이 "지금 켜져 있나요?"에 **모른다고** 답하게 해야 한다.
- **LG 의 "남은 시간"은 종료 *시각*이다.** `finish_at` 은 `2026-09-13T10:20:51+00:00`
  같은 ISO 타임스탬프다. "몇 분 남았어?"에 답하려면 현재 시각과 빼야 한다.
- **범위 밖 값은 400 이다.** 에어컨 온도 40℃ 같은 명령은 어댑터가 막는다.

## 7. 개발

```bash
pip install -r requirements-dev.txt
pytest          # 29개
```

HA 없이도 전부 돈다 — `FakeHaClient` 가 서비스 호출을 기록한다.
