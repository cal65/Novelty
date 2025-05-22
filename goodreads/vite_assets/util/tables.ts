import type { Table } from "@tanstack/react-table";

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
