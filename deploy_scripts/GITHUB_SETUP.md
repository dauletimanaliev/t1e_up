# 📱 Создание GitHub репозитория

## 1. Создайте репозиторий на GitHub
1. Зайдите на [github.com](https://github.com)
2. Нажмите "New repository"
3. Название: `t1eup-web`
4. Сделайте публичным
5. Нажмите "Create repository"

## 2. Подключите локальный репозиторий
```bash
git remote add origin https://github.com/YOUR_USERNAME/t1eup-web.git
git branch -M main
git push -u origin main
```

## 3. Деплой готов!
Теперь можете использовать любой из вариантов деплоя:
- Heroku: `./quick_deploy.sh`
- Railway: `./railway_deploy.sh`
- Render: следуйте `render_deploy.md`
- VPS: `./vps_deploy.sh`

## 🎉 Ваш сайт будет работать!
