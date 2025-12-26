# API Documentation: Conversations

이 문서는 Overmind API의 대화(Conversation) 관련 엔드포인트(`/api/conversations`)에 대한 명세를 제공합니다.

## Base URL

`http://<your_host>/api/conversations`

## Authentication

모든 엔드포인트는 `Authorization` 헤더에 `Bearer <JWT_TOKEN>` 형식의 유효한 JWT 토큰을 필요로 합니다.

---

## 1. 대화 시작 또는 이어하기

새로운 대화를 시작하거나, 해당 날짜에 이미 진행 중인 활성 대화가 있다면 그 대화를 이어갑니다.

- **Endpoint:** `POST /`
- **Summary:** Start new conversation
- **Description:** AI가 생성한 인사말과 함께 새로운 일기 대화 세션을 시작하거나 기존 대화를 가져옵니다.

### Request Body

- **Content-Type:** `application/json`

| Field          | Type      | Required | Default                 | Description                                                                                                                              |
| -------------- | --------- | -------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `entry_date`   | `string`  | Yes      |                         | 이 일기가 작성될 날짜 (형식: `YYYY-MM-DD`).                                                                                                   |
| `timezone`     | `string`  | No       | `America/Los_Angeles`   | 사용자의 타임존 (IANA 형식, 예: `Asia/Seoul`).                                                                                                |
| `current_time` | `string`  | No       | `null`                  | 클라이언트의 현재 시각 (ISO 8601 형식). 제공되지 않으면 서버 시각을 사용합니다.                                                                     |
| `force_new`    | `boolean` | No       | `false`                 | `true`로 설정하면, 해당 날짜에 활성 대화가 있더라도 강제로 완료 처리하고 새로운 대화를 시작합니다. |

**Example Request:**

```json
{
  "entry_date": "2025-12-25",
  "timezone": "Asia/Seoul",
  "current_time": "2025-12-25T14:30:00+09:00",
  "force_new": false
}
```

### Responses

- **`201 Created`**: 새로운 대화가 성공적으로 생성되었을 때.
- **`200 OK`**: 기존 활성 대화를 성공적으로 불러왔을 때.

**Response Body (`ConversationResponse`):**

```json
{
  "id": 101,
  "user_id": 1,
  "entry_date": "2025-12-25",
  "status": "active",
  "started_at": "2025-12-25T05:30:00Z",
  "ended_at": null,
  "messages": [
    {
      "id": 201,
      "role": "ai",
      "content": "안녕하세요! 오늘 하루는 어떠셨나요?",
      "created_at": "2025-12-25T05:30:01Z",
      "image_url": null
    }
  ]
}
```

---

## 2. 특정 날짜의 활성 대화 조회

특정 날짜에 진행 중인 활성 대화의 전체 내용을 조회합니다.

- **Endpoint:** `GET /active`
- **Summary:** Get active conversation
- **Description:** 사용자의 특정 날짜에 대한 현재 활성화된 대화 내용을 가져옵니다.

### Query Parameters

| Parameter    | Type     | Required | Description                             |
| ------------ | -------- | -------- | --------------------------------------- |
| `entry_date` | `string` | Yes      | 조회할 일기의 날짜 (형식: `YYYY-MM-DD`). |

**Example Request:**

`GET /api/conversations/active?entry_date=2025-12-25`

### Responses

- **`200 OK`**: 활성 대화를 성공적으로 찾았을 때.
- **`404 Not Found`**: 해당 날짜에 활성 대화가 없을 때.

**Response Body (`ConversationResponse`):**
(위의 `ConversationResponse`와 동일)

---

## 3. 메시지 전송

진행 중인 대화에 새로운 메시지를 보내고 AI의 답변을 받습니다.

- **Endpoint:** `POST /{conversation_id}/messages`
- **Summary:** Send message
- **Description:** 사용자가 메시지를 보내고 AI의 응답을 수신합니다.

### Path Parameters

| Parameter         | Type      | Description             |
| ----------------- | --------- | ----------------------- |
| `conversation_id` | `integer` | 메시지를 보낼 대화의 ID. |

### Request Body

- **Content-Type:** `application/json`

| Field   | Type     | Required | Description            |
| ------- | -------- | -------- | ---------------------- |
| `content` | `string` | Yes      | 보낼 메시지의 내용.      |

**Example Request:**

```json
{
  "content": "오늘 정말 즐거운 하루였어요."
}
```

### Responses

- **`200 OK`**: AI가 성공적으로 응답했을 때.

**Response Body (`AIMessageResponse`):**

```json
{
  "message_id": 203,
  "content": "정말 즐거운 하루셨다니 저도 기쁘네요! 어떤 점이 가장 즐거우셨나요?",
  "created_at": "2025-12-25T05:32:15Z",
  "quality_info": {
    "is_sufficient": false,
    "quality_level": "insufficient",
    "user_message_count": 1,
    "total_user_content_length": 15,
    "avg_user_message_length": 15.0,
    "feedback_message": "2개의 메시지가 더 필요해요, 조금 더 자세히 이야기해주세요. 더 이야기를 나눠볼까요?"
  }
}
```
---

## 4. 대화 완료하기

현재 진행 중인 대화를 '완료' 상태로 변경합니다. 이 대화로는 더 이상 메시지를 보낼 수 없게 됩니다.

- **Endpoint:** `POST /{conversation_id}/complete`
- **Summary:** Complete conversation
- **Description:** 대화를 완료 상태로 표시합니다. 이 작업을 해야 같은 날짜에 새로운 대화를 시작할 수 있습니다.

### Path Parameters

| Parameter         | Type      | Description             |
| ----------------- | --------- | ----------------------- |
| `conversation_id` | `integer` | 완료할 대화의 ID. |

### Responses

- **`200 OK`**: 대화가 성공적으로 완료되었을 때.

**Response Body (`ConversationResponse`):**
(상태가 `completed`로 변경되고 `ended_at`이 설정된 `ConversationResponse` 객체)
