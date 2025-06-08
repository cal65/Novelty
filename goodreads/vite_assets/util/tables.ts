import type { Table } from "@tanstack/react-table";
import { stringify } from "csv-stringify/browser/esm/sync";
import FileSaver from "file-saver";

export function saveToCsv<TData>(table: Table<TData>, fileName: string) {
  // Include all rows after applying filters and sorting, ignoring pagination
  const rows = table.getPrePaginationRowModel().rows;

  const headers = table.getVisibleFlatColumns().map((col) => col.id);
  const csvContent = stringify([
    headers,
    ...rows.map((row) => headers.map((header) => row.getValue(header))),
  ]);

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  FileSaver.saveAs(blob, fileName);
}

export function updatePageSize<TData>(
  table: Table<TData>,
  pageSizeValue: string | null,
) {
  if (pageSizeValue === null) {
    return;
  }
  const newPageSize = Number.parseInt(pageSizeValue, 10);
  table.setPagination(({ pageIndex, pageSize }) => {
    const newPageIndex = Math.floor((pageIndex * pageSize) / newPageSize);
    return {
      pageIndex: newPageIndex,
      pageSize: newPageSize,
    };
  });
}
