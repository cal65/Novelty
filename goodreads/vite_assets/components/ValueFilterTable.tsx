import { ActionIcon, Table } from "@mantine/core";
import {
  IconCaretDown,
  IconCaretUp,
  IconCaretUpDown,
} from "@tabler/icons-react";
import {
  type Row,
  type RowData,
  type RowSelectionState,
  type Table as TanstackTable,
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  type VirtualItem,
  type Virtualizer,
  useVirtualizer,
} from "@tanstack/react-virtual";
import { type SetStateAction, useEffect, useMemo, useState } from "react";
import { isArray, sumBy } from "remeda";
import { twMerge } from "tailwind-merge";
import SearchInput from "./SearchInput.tsx";

export type Props<TData> = {
  table: TanstackTable<TData>;
  columnId: string;
  rowSelection: RowSelectionState;
  setRowSelection: (updater: SetStateAction<RowSelectionState>) => void;
  collapsed?: boolean;
};

export default function ValueFilterTable<TData, TValue>({
  table,
  columnId,
  rowSelection,
  setRowSelection,
  collapsed = false,
}: Props<TData>) {
  const filterData = useMemo(() => {
    const counts = new Map<TValue, number>();
    for (const item of table.getCoreRowModel().rows) {
      const value = item.getValue(columnId) as TValue | TValue[];
      if (isArray(value)) {
        for (const val of value) {
          counts.set(val, (counts.get(val) || 0) + 1);
        }
      } else {
        counts.set(value, (counts.get(value) || 0) + 1);
      }
    }
    return Array.from(counts, ([value, count]) => ({
      value,
      count,
    }));
  }, [table, columnId]);

  const columnHelper = useMemo(
    () => createColumnHelper<{ value: TValue; count: number }>(),
    [],
  );

  const columns = useMemo(
    () => [
      columnHelper.accessor("value", {
        header:
          (table.getColumn(columnId)?.columnDef.header as string | undefined) ??
          "Value",
        cell: (info) =>
          info.getValue() || <span className="italic">No data</span>,
        filterFn: "includesString",
        sortingFn: "basic",
        minSize: 250,
      }),
      columnHelper.accessor("count", {
        header: "Count",
        cell: (info) => info.getValue(),
        sortingFn: "basic",
        maxSize: 90,
        enableColumnFilter: false,
        meta: {
          cellClassName: "text-right",
        },
      }),
    ],
    [columnHelper, table, columnId],
  );

  // The virtualizer will need a reference to the scrollable container element.
  // Initially, I tried using `useRef` here, but that didn't work on the first render because React doesn't
  // re-render when a ref changes.
  const [tableContainer, setTableContainer] = useState<HTMLDivElement | null>(
    null,
  );

  const filterTable = useReactTable({
    data: filterData,
    columns,
    enableRowSelection: true,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onRowSelectionChange: setRowSelection,
    initialState: {
      sorting: [
        {
          id: "count",
          desc: true,
        },
      ],
    },
    state: {
      rowSelection,
    },
  });

  // React to changes in row selection
  useEffect(() => {
    const selectedValues: TValue[] = [];
    const rowsById = filterTable.getCoreRowModel().rowsById;
    for (const rowId in rowSelection) {
      if (rowSelection[rowId]) {
        const row = rowsById[rowId];
        selectedValues.push(row.getValue("value") as TValue);
      }
    }
    table
      .getColumn(columnId)
      ?.setFilterValue(selectedValues.length ? selectedValues : null);
  }, [filterTable, rowSelection, table, columnId]);

  const tableWidth =
    15 + sumBy(filterTable.getVisibleLeafColumns(), (col) => col.getSize());

  return (
    <div className="border border-gray-200" style={{ width: tableWidth }}>
      <Table fz="xs">
        <Table.Thead>
          <Table.Tr className="flex w-full">
            {filterTable.getFlatHeaders().map((header) => {
              const column = header.column;
              const sorted = header.column.getIsSorted();
              const searchValue = (column.getFilterValue() as string) ?? "";

              return (
                <Table.Th key={column.id} style={{ width: column.getSize() }}>
                  <div className="flex justify-between items-center gap-x-2">
                    <div className="text-nowrap">
                      {flexRender(column.columnDef.header, header.getContext())}
                    </div>
                    {column.getCanFilter() && (
                      <SearchInput
                        placeholder="Filter"
                        value={searchValue}
                        onChange={(value) => column.setFilterValue(value)}
                      />
                    )}
                    {column.getCanSort() && (
                      <ActionIcon
                        variant="default"
                        onClick={column.getToggleSortingHandler()}
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
        </Table.Thead>
      </Table>
      {!collapsed && (
        <div className="overflow-auto relative h-64" ref={setTableContainer}>
          <Table className="grid" fz="xs">
            <TableBody table={filterTable} tableContainer={tableContainer} />
          </Table>
        </div>
      )}
    </div>
  );
}

type TableBodyProps<TData extends RowData> = {
  table: TanstackTable<TData>;
  tableContainer: HTMLDivElement | null;
};

function TableBody<TData>({ table, tableContainer }: TableBodyProps<TData>) {
  const { rows } = table.getRowModel();

  // Important: Keep the row virtualizer in the lowest component possible to avoid unnecessary re-renders.
  const rowVirtualizer = useVirtualizer<HTMLDivElement, HTMLTableRowElement>({
    count: rows.length,
    estimateSize: () => 33.6, // estimate row height for accurate scrollbar dragging
    getScrollElement: () => tableContainer,
    getItemKey: (index) => rows[index].id, // use row id as key
    // measure dynamic row height, except in firefox because it measures table border height incorrectly
    measureElement:
      typeof window !== "undefined" &&
      navigator.userAgent.indexOf("Firefox") === -1
        ? (element) => element?.getBoundingClientRect().height
        : undefined,
    overscan: 5,
  });

  return (
    <Table.Tbody
      className="grid relative"
      style={{ height: rowVirtualizer.getTotalSize() }}
    >
      {rowVirtualizer.getVirtualItems().map((virtualRow) => {
        const row = rows[virtualRow.index];
        return (
          <TableRow
            key={row.id}
            row={row}
            virtualRow={virtualRow}
            rowVirtualizer={rowVirtualizer}
          />
        );
      })}
    </Table.Tbody>
  );
}

type TableRowProps<TData extends RowData> = {
  row: Row<TData>;
  virtualRow: VirtualItem;
  rowVirtualizer: Virtualizer<HTMLDivElement, HTMLTableRowElement>;
};

function TableRow<TData>({
  row,
  virtualRow,
  rowVirtualizer,
}: TableRowProps<TData>) {
  return (
    <Table.Tr
      data-index={virtualRow.index} //needed for dynamic row height measurement
      ref={(node) => rowVirtualizer.measureElement(node)} //measure dynamic row height
      className="flex absolute w-full"
      style={{
        transform: `translateY(${virtualRow.start}px)`, //this should always be a `style` as it changes on scroll
      }}
    >
      {row.getVisibleCells().map((cell) => {
        return (
          <Table.Td
            key={cell.id}
            onClick={row.getToggleSelectedHandler()}
            className={twMerge(
              "cursor-pointer",
              row.getIsSelected() && "bg-blue-500",
              cell.column.columnDef.meta?.cellClassName,
            )}
            style={{ width: cell.column.getSize() }}
          >
            {flexRender(cell.column.columnDef.cell, cell.getContext())}
          </Table.Td>
        );
      })}
    </Table.Tr>
  );
}
