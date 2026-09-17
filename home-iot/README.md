# home-iot / home-core

Home Assistant 위에 올리는 **기기 추상화 계층**. HA 엔티티를 사람이 말하는 단위
(기기 · 방 · 능력)로 정리해서 대시보드와 LLM이 안전하게 쓰도록 한다.

## 왜 필요한가

HA 엔티티는 기기 단위가 아니라 능력 단위로 흩어져 있다. 특히 Aqara E1 스위치는
Matter 씬으로만 제어되기 때문에 **한 논리 기기가 두 엔티티(켜기 씬 / 끄기 씬)로
쪼개진다.** 그 위에 `on_off` 하나를 올리는 게 이 프로젝트의 핵심이다.

## 설계 원칙 세 가지

1. **명령은 멱등해야 한다.** 토글 씬은 쓰지 않는다. `on_off=false` 를 몇 번
   보내도 "끄기 씬"만 실행된다. 토글이면 이미 꺼진 날 밤 11시 자동화가 **불을
   켠다.**
2. **모르는 상태는 지어내지 않는다.** 씬 스위치는 실행 후 항상 `off` 로
   돌아간다. 그걸 "조명 꺼짐"으로 내보내면 대시보드와 LLM이 틀린 정보를 믿는다.
   읽을 엔티티가 없는 능력은 상태를 **아예 보고하지 않는다.**
3. **단위는 도메인 쪽에 맞춘다.** 밝기는 0~100 으로 내보내고, HA 의 0~255 는
   어댑터가 변환한다.

## 실행

```bash
pip install -r requirements.txt
cp .env.example .env        # HA_URL, HA_TOKEN 채우기
uvicorn home_core.api:create_app --factory --reload
```

## API

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/health` | 기기·방 개수 |
| GET | `/devices` | 기기 목록 + 능력 + 현재 상태 |
| GET | `/state` | 전체 상태 스냅샷 |
| POST | `/refresh` | HA 를 즉시 재조회 |
| POST | `/devices/{id}/command` | `{"capability": "on_off", "value": false}` |
| GET | `/events` | SSE 상태·명령 스트림 |
| GET | `/history` | 이력 (타입별 컬럼) |

## 테스트

```bash
pip install -r requirements-dev.txt
pytest
```

자세한 사용법은 [docs/USER_GUIDE.md](docs/USER_GUIDE.md), 기기 현황과 한계는
[docs/DEVICE_INVENTORY.md](docs/DEVICE_INVENTORY.md).
