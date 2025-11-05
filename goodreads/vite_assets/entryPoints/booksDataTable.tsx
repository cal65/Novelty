import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@mantine/core/styles.css";
import { MantineProvider } from "@mantine/core";
import BooksDataTable from "../components/BooksDataTable.tsx";
import theme from "../util/theme.ts";

const scriptUrlParams = new URL(import.meta.url).searchParams;
const propsElementId = scriptUrlParams.get("elementId") ?? "reactPropsElement";
const propsElement = document.getElementById(propsElementId);
if (propsElement) {
  // Parse the JSON props from the element's text content, and then render the component in a div
  // that is inserted after the props element.
  const props = JSON.parse(propsElement.textContent ?? "");
  const rootElement = document.createElement("div");
  propsElement.after(rootElement);
  createRoot(rootElement).render(
    <StrictMode>
      <MantineProvider theme={theme}>
        <BooksDataTable {...props} />
      </MantineProvider>
    </StrictMode>,
  );
} else {
  console.error(`dataTable: element with id ${propsElementId} not found.`);
}
