import type {Table} from "@tanstack/react-table";
import {Group, Pagination} from '@mantine/core';


export type Props<T> = {
  table: Table<T>;
}

export function PaginationControls<T>({table}: Props<T>) {
  // Note that Mantine's Pagination widget is 1-indexed, while Tanstack Table is 0-indexed
  const {pagination} = table.getState();
  return (
      <Pagination
          value={pagination.pageIndex + 1}
          total={table.getPageCount()}
          onChange={value => table.setPageIndex(value - 1)}
          onNextPage={table.nextPage}
          onPreviousPage={table.previousPage}
          size="sm"
          withEdges
          />
  );
}
