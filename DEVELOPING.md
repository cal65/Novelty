# Instructions on how to develop Novelty

## Local setup

1. Install `uv` for Python package management following the [instructions](https://docs.astral.sh/uv/getting-started/installation/)
2. Install `node` for JS package management following the [instructions](https://nodejs.org/en/download/)
3. Run `uv sync` to install Python dependencies. 
   * This will make a virtual environment at `.venv`, which you can activate by running `. .venv/bin/activate` in your shell
4. Run `npm install` to install JS dependencies
4. Run `npm run dev` to start a server for frontend assets (including Tailwind CSS)
5. Run `uv run manage.py runserver` to start the Django server

Not included in these instructions: setting up the database. It would be easiest to restore the database from a backup,
but you can also run `uv run manage.py migrate` to create the database and tables from scratch.


## Deploying to production

1. ssh to the production webserver and pull from git
2. Run `npm install` and `npm run build` to install and build frontend assets
3. Kill gunicorn if it's already running: `pkill gunicorn`
4. Run `./scripts/run_production.sh` to start the server



# Frontend instructions

## React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default tseslint.config({
  extends: [
    // Remove ...tseslint.configs.recommended and replace with this
    ...tseslint.configs.recommendedTypeChecked,
    // Alternatively, use this for stricter rules
    ...tseslint.configs.strictTypeChecked,
    // Optionally, add this for stylistic rules
    ...tseslint.configs.stylisticTypeChecked,
  ],
  languageOptions: {
    // other options...
    parserOptions: {
      project: ['./tsconfig.node.json', './tsconfig.app.json'],
      tsconfigRootDir: import.meta.dirname,
    },
  },
})
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config({
  plugins: {
    // Add the react-x and react-dom plugins
    'react-x': reactX,
    'react-dom': reactDom,
  },
  rules: {
    // other rules...
    // Enable its recommended typescript rules
    ...reactX.configs['recommended-typescript'].rules,
    ...reactDom.configs.recommended.rules,
  },
})
```
