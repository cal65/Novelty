import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  type Row,
  type RowData,
  useReactTable
} from "@tanstack/react-table";
import '@tanstack/react-table';
import {fetcher} from "../util/fetcher.ts";
import useSWR from "swr";
import {ActionIcon, Table} from "@mantine/core";
import {PaginationControls} from "./PaginationControls.tsx";
import {formatNumber} from "../util/formatting.ts";
import {IconCaretDown, IconCaretUp, IconCaretUpDown} from "@tabler/icons-react";
import {memo} from "react";


declare module '@tanstack/react-table' {
  interface ColumnMeta<TData extends RowData, TValue> {
    width?: number | string;
  }
}

export type Props = {
  url: string;
}

type Book = {
  title_simple: string;
  author: string;
  gender: string;
  nationality_chosen: string;
  original_publication_year: number;
  read: number;
  narrative: string;
  shelves: string[];
  number_of_pages: number;
}

const columnHelper = createColumnHelper<Book>()

const mainColumns = [
  columnHelper.accessor('title_simple', {
    header: 'Title',
    cell: (info) => info.getValue(),
    meta: {
      width: '22%'
    }
  }),
  columnHelper.accessor('author', {
    header: 'Author',
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor('gender', {
    header: 'Gender',
    cell: (info) => info.getValue(),
    meta: {
      width: '7rem'
    }
  }),
  columnHelper.accessor('nationality_chosen', {
    header: 'Nationality',
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor('original_publication_year', {
    header: 'Year',
    cell: (info) => info.getValue(),
    meta: {
      width: '6rem'
    }
  }),
  columnHelper.accessor('read', {
    header: 'Readers',
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor('narrative', {
    header: 'Narrative',
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor('shelves', {
    header: 'Shelves',
    cell: (info) => info.getValue().join(', '),
    meta: {
      width: '22%'
    }
  }),
  columnHelper.accessor('number_of_pages', {
    header: '# of Pages',
    cell: (info) => info.getValue(),
  }),
]

const BookRow = memo(({row}: { row: Row<Book> }) => (
        <Table.Tr>
          {row.getVisibleCells().map(cell => (
              <Table.Td key={cell.id}>
                {flexRender(
                    cell.column.columnDef.cell,
                    cell.getContext()
                )}
              </Table.Td>
          ))}
        </Table.Tr>
    )
);


export default function BooksDataTable({url}: Props) {
  const {data, error, isLoading} = useSWR<Book[]>(url, fetcher);

  const table = useReactTable({
    data: data ?? [],
    columns: mainColumns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    initialState: {
      pagination: {
        pageIndex: 0,
        pageSize: 25
      }
    },
  });
  const {pagination} = table.getState();
  const {rows} = table.getFilteredRowModel();

  if (error) {
    return <div>failed to load</div>
  }
  if (isLoading) {
    return <div>loading...</div>
  }
  if (!data) {
    return <div>No data</div>
  }

  return (
      <div className="mx-2">
        <Table withTableBorder withColumnBorders className="w-full" layout="fixed">
          <Table.Thead>
            {table.getHeaderGroups().map(headerGroup => (
                <Table.Tr key={headerGroup.id}>
                  {headerGroup.headers.map(header => (
                      <Table.Th key={header.id} style={{width: header.column.columnDef.meta?.width ?? 'auto'}}>
                        <div className="flex justify-between items-center gap-x-2">
                          {header.isPlaceholder
                              ? null
                              : flexRender(
                                  header.column.columnDef.header,
                                  header.getContext()
                              )}
                          {header.column.getCanSort() && (
                              <ActionIcon
                                  variant="default"
                                  onClick={header.column.getToggleSortingHandler()}
                              >
                                {header.column.getIsSorted()
                                    ? header.column.getIsSorted() === "desc"
                                        ? <IconCaretDown size={12}/>
                                        : <IconCaretUp size={12}/>
                                    : <IconCaretUpDown size={12}/>}
                              </ActionIcon>
                          )}
                        </div>
                      </Table.Th>
                  ))}
                </Table.Tr>
            ))}
          </Table.Thead>
          <Table.Tbody>{
            table.getRowModel().rows.map(row => <BookRow key={row.id} row={row}/>)
          }</Table.Tbody>
        </Table>
        <div className="flex justify-between text-sm my-2">
          <div>
            Showing entries {pagination.pageIndex * pagination.pageSize + 1}
            {" "}to{" "}
            {Math.min((pagination.pageIndex + 1) * pagination.pageSize, rows.length)} of{" "}
            {formatNumber(rows.length)} entries
          </div>
          <PaginationControls table={table}/>
        </div>
      </div>
  );
}