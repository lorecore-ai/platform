# Vault и LangChain: хранение OpenAI API ключа

Платформа использует HashiCorp Vault для хранения секретов, включая API-ключ OpenAI. LangChain-сервис получает ключ из Vault при каждом стриминговом ответе.

## Как это работает

### Поток получения ключа

При запросе ответа LLM (`stream_response`) сервис выполняет:

1. **LangChainService** получает `SecretsManager` (VaultSecretsManager) через DI.
2. Вызывается `_get_openai_api_key(tenant_id)` с учётом контекста tenant.
3. Ключ ищется в таком порядке:
   - `integrations/{tenant_id}/openai` — ключ, привязанный к tenant;
   - `integrations/platform/openai` — общий ключ платформы;
   - `OPENAI_API_KEY` из переменных окружения — fallback.

4. Ключ передаётся в `ChatOpenAI` при создании экземпляра LLM.

### Структура путей в Vault

- **Mount point** (engine): `secret` — стандартный mount KV v2 в dev-режиме.
- **Secret path** — путь внутри mount:
  - для tenant: `integrations/{tenant_id}/openai`
  - для платформы: `integrations/platform/openai`

Полный путь в CLI: `secret/integrations/platform/openai`.

### Конфигурация

Переменные окружения (`infra/docker/.env`):

| Переменная      | Описание                          | По умолчанию          |
|-----------------|-----------------------------------|------------------------|
| `VAULT_URL`     | URL Vault                         | `http://vault:8200`    |
| `VAULT_TOKEN`   | Токен для доступа к Vault         | —                      |
| `OPENAI_API_KEY`| Fallback, если ключа нет в Vault  | —                      |

---

## Как добавить OpenAI ключ в Vault

### Предварительные условия

- Запущен Vault (например, через `docker-compose up -d vault`).
- Установлен [Vault CLI](https://developer.hashicorp.com/vault/docs/install) или доступ к контейнеру с Vault.

### Вариант 1: платформенный ключ (для всех tenant)

Один ключ для всей платформы:

```bash
# Настроить адрес и токен (если не через env)
export VAULT_ADDR='http://localhost:8200'
export VAULT_TOKEN='root'

# Записать ключ
vault kv put secret/integrations/platform/openai api_key="sk-your-openai-key-here"
```

Через контейнер Docker:

```bash
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=root vault \
  vault kv put secret/integrations/platform/openai api_key="sk-your-key"
```

### Вариант 2: ключ для конкретного tenant

Отдельный ключ для tenant (например, `tenant_id = 550e8400-e29b-41d4-a716-446655440000`):

```bash
vault kv put secret/integrations/550e8400-e29b-41d4-a716-446655440000/openai api_key="sk-tenant-specific-key"
```

### Вариант 3: через hvac (Python)

```python
import hvac

client = hvac.Client(url="http://localhost:8200", token="root")
client.secrets.kv.v2.create_or_update_secret(
    path="integrations/platform/openai",
    mount_point="secret",
    secret={"api_key": "sk-your-key"},
)
```

### Проверка

```bash
vault kv get secret/integrations/platform/openai
```

Ожидаемый вывод (в упрощённом виде):

```
====== Metadata ======
...
====== Data ======
Key       Value
---       -----
api_key   sk-***
```

---

## Fallback на переменные окружения

Если ключ не найден ни в Vault для tenant, ни для `platform`, используется переменная окружения `OPENAI_API_KEY`. Это удобно для локальной разработки без Vault.

---

## Связанные файлы

- `app/modules/threads/langchain_service.py` — `_get_openai_api_key`, `stream_response`
- `app/modules/secrets/vault.py` — `VaultSecretsManager`
- `app/modules/secrets/bootstrap.py` — инициализация Vault при старте приложения
- `infra/docker/.env.example` — пример конфигурации
