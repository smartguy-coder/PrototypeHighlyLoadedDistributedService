# Storefront Catalog Service — Frontend

Веб-інтерфейс для сервісу каталогу товарів, частина прототипу високонавантаженої розподіленої системи.

## 🛠 Технології

| Категорія | Технологія | Версія |
|-----------|------------|--------|
| **Runtime** | React | 19.2 |
| **Мова** | TypeScript | 5.9 |
| **Збірка** | Vite | 7.3 |
| **UI-бібліотека** | Material UI | 7.3 |
| **Маршрутизація** | React Router | 7.13 |
| **HTTP-клієнт** | Axios | 1.13 |
| **Лінтинг** | ESLint | 9.39 |

## 📋 Передумови

- **Node.js** ≥ 20.x
- **npm** ≥ 10.x (або yarn/pnpm)
- Запущений backend-сервіс `storefront_catalog_service`

## 🚀 Швидкий старт

```bash
# Перейти до директорії з додатком
cd app

# Встановити залежності
npm install

# Запустити dev-сервер
npm run dev
```

Додаток буде доступний за адресою: **http://localhost:5173**

## 📜 Доступні скрипти

| Команда | Опис |
|---------|------|
| `npm run dev` | Запуск dev-сервера з HMR |
| `npm run build` | Компіляція TypeScript + production-збірка |
| `npm run preview` | Локальний перегляд production-збірки |
| `npm run lint` | Перевірка коду ESLint |

## 🧪 Розробка

### Рекомендований стек інструментів

- **IDE**: VS Code з розширеннями:
  - ESLint
  - Prettier
  - TypeScript Vue Plugin (Volar)
  
- **Браузер**: Chrome/Firefox з React DevTools

### Code Style

Проєкт використовує ESLint для підтримки якості коду:

```bash
# Перевірка
npm run lint

# Автовиправлення (якщо налаштовано)
npm run lint -- --fix
```

## 📚 Корисні посилання

- [Vite Documentation](https://vite.dev/)
- [React Documentation](https://react.dev/)
- [Material UI](https://mui.com/material-ui/)
- [React Router](https://reactrouter.com/)
- [Axios](https://axios-http.com/)
