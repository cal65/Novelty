import {join, resolve} from 'node:path';
import {defineConfig, loadEnv} from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite'


// https://vite.dev/config/
export default defineConfig(({mode}) => {
    const env = loadEnv(mode, process.cwd(), '');

    const INPUT_DIR = './goodreads/vite_assets';
    const OUTPUT_DIR = join(INPUT_DIR, '/dist');

    return {
        plugins: [
            react(),
            tailwindcss(),
        ],
        root: resolve(INPUT_DIR),

        base: "/static/",
        server: {
            host: env.DJANGO_VITE_DEV_SERVER_HOST,
            port: parseInt(env.DJANGO_VITE_DEV_SERVER_PORT, 10),
        },
        build: {
            manifest: "manifest.json",
            emptyOutDir: true,
            outDir: resolve(OUTPUT_DIR),
            rollupOptions: {
                input: {
                    main: join(INPUT_DIR, '/apps/main.tsx'),
                    css: join(INPUT_DIR, '/css/main.css.ts'),
                }
            }

        }
    };
})
