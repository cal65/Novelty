import { ActionIcon, Table } from "@mantine/core";
import {
  IconCaretDown,
  IconCaretUp,
  IconCaretUpDown,
} from "@tabler/icons-react";
import {
  type RowData,
  type Table as TanstackTable,
  flexRender,
} from "@tanstack/react-table";
import clsx from "clsx";
import { PaginationControl } from "./PaginationControl.tsx";

declare module "@tanstack/react-table" {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface ColumnMeta<TData extends RowData, TValue> {
    cellClassName?: string;
  }
}

export type Props<T> = {
  table: TanstackTable<T>;
  containerClass?: string;
};

export default function DataTable<T>({ table, containerClass }: Props<T>) {
  return (
    <div className={clsx(containerClass)}>
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
      <PaginationControl table={table} />
    </div>
  );
}
