import type { Row, RowData } from "@tanstack/react-table";
import { intersection } from "remeda";

export function equalsAny<TData extends RowData, TValue>(
  row: Row<TData>,
  columnId: string,
  filterValue: TValue[],
): boolean {
  const columnValue = row.getValue<TValue | null>(columnId);
  return (
    columnValue !== null &&
    (filterValue === null || filterValue.includes(columnValue))
  );
}

export function arrIncludesAny<TData extends RowData, TValue>(
  row: Row<TData>,
  columnId: string,
  filterValue: TValue[] | null,
): boolean {
  const columnValues = row.getValue<TValue[] | null>(columnId);
  return (
    columnValues !== null &&
    (filterValue === null || intersection(filterValue, columnValues).length > 0)
  );
}
