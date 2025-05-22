import {StrictMode} from 'react'
import {createRoot} from 'react-dom/client'
import '@mantine/core/styles.css';
import {MantineProvider} from "@mantine/core";
import BooksDataTable from "../components/BooksDataTable.tsx";

const scriptUrlParams = new URL(import.meta.url).searchParams;
const propsElementId = scriptUrlParams.get('elementId') ?? 'reactPropsElement';
const propsElement = document.getElementById(propsElementId);
if (propsElement) {
  const props = JSON.parse(propsElement.textContent ?? '');
  const rootElement = document.createElement('div');
  propsElement.after(rootElement);
  createRoot(rootElement).render(
      <StrictMode>
        <MantineProvider>
          <BooksDataTable {...props} />
        </MantineProvider>
      </StrictMode>,
  )
} else {
  console.error(`dataTable: element with id ${propsElementId} not found.`);
}
