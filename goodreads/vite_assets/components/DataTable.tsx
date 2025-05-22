import { ActionIcon, Table } from "@mantine/core";
import {
  flexRender,
  type RowData,
  type Table as TanstackTable,
} from "@tanstack/react-table";
import {
  IconCaretDown,
  IconCaretUp,
  IconCaretUpDown,
} from "@tabler/icons-react";
import { PaginationControls } from "./PaginationControls.tsx";
import { twMerge } from "tailwind-merge";

declare module "@tanstack/react-table" {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface ColumnMeta<TData extends RowData, TValue> {
    cellClassName?: string;
  }
}

export type Props<T> = {
  table: TanstackTable<T>;
  pagination?: boolean;
  virtualized?: boolean;
  containerClass?: string;
};

export default function DataTable<T>({
  table,
  pagination,
  containerClass,
}: Props<T>) {
  return (
    <div className={twMerge("mx-2", containerClass)}>
      <Table
        withTableBorder
        withColumnBorders
        className="w-full"
        layout="fixed"
      >
        <Table.Thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <Table.Tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                const sorted = header.column.getIsSorted();
                return (
                  <Table.Th
                    key={header.id}
                    style={{ width: header.column.getSize() }}
                  >
                    <div className="flex justify-between items-center gap-x-2">
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                      {header.column.getCanSort() && (
                        <ActionIcon
                          variant="default"
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {sorted ? (
                            sorted === "desc" ? (
                              <IconCaretDown size={12} />
                            ) : (
                              <IconCaretUp size={12} />
                            )
                          ) : (
                            <IconCaretUpDown size={12} />
                          )}
                        </ActionIcon>
                      )}
                    </div>
                  </Table.Th>
                );
              })}
            </Table.Tr>
          ))}
        </Table.Thead>
        <Table.Tbody>
          {table.getRowModel().rows.map((row) => (
            <Table.Tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <Table.Td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </Table.Td>
              ))}
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
      {pagination && <PaginationControls table={table} />}
    </div>
  );
}
