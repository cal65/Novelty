import { Pagination } from "@mantine/core";
import type { Table } from "@tanstack/react-table";
import { formatNumber } from "../util/formatting.ts";

type Props<TData> = {
  table: Table<TData>;
};

export function PaginationControl<TData>({ table }: Props<TData>) {
  // Note that Mantine's Pagination widget is 1-indexed, while Tanstack Table is 0-indexed
  const { pagination } = table.getState();
  const { rows } = table.getFilteredRowModel();
  return (
    <div className="flex justify-between text-sm my-2">
      {rows.length ? (
        <div>
          Showing entries {pagination.pageIndex * pagination.pageSize + 1} to{" "}
          {Math.min(
            (pagination.pageIndex + 1) * pagination.pageSize,
            rows.length,
          )}{" "}
          of {formatNumber(rows.length)} entries
        </div>
      ) : (
        <div>Showing 0 entries</div>
      )}
      <Pagination
        value={pagination.pageIndex + 1}
        total={table.getPageCount()}
        onChange={(value) => table.setPageIndex(value - 1)}
        onNextPage={table.nextPage}
        onPreviousPage={table.previousPage}
        size="sm"
        withEdges
      />
    </div>
  );
}
