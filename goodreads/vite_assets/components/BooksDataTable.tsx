import {
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  type RowSelectionState,
  useReactTable,
} from "@tanstack/react-table";
import "@tanstack/react-table";
import { fetcher } from "../util/fetcher.ts";
import DataTable from "./DataTable.tsx";
import useSWR from "swr";
import ValueFilterTable from "./ValueFilterTable.tsx";
import { arrIncludesAny, equalsAny } from "./filterFunctions.ts";
import { useCallback, useState } from "react";
import { sumBy } from "remeda";
import { Button } from "@mantine/core";
import {
  IconArrowsDiagonal2,
  IconArrowsDiagonalMinimize,
  IconX,
} from "@tabler/icons-react";

export type Props = {
  url: string;
};

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
};

const columnHelper = createColumnHelper<Book>();

const mainColumns = [
  columnHelper.accessor("title_simple", {
    header: "Title",
    cell: (info) => info.getValue(),
    minSize: 300,
    sortingFn: "alphanumeric",
  }),
  columnHelper.accessor("author", {
    header: "Author",
    cell: (info) => info.getValue(),
    filterFn: equalsAny,
    sortingFn: "text",
  }),
  columnHelper.accessor("gender", {
    header: "Gender",
    cell: (info) => info.getValue(),
    filterFn: equalsAny,
    sortingFn: "text",
    size: 80,
  }),
  columnHelper.accessor("nationality_chosen", {
    header: "Nationality",
    cell: (info) => info.getValue(),
    filterFn: equalsAny,
    sortingFn: "basic",
  }),
  columnHelper.accessor("original_publication_year", {
    header: "Year",
    cell: (info) => info.getValue(),
    filterFn: equalsAny,
    sortingFn: "basic",
    size: 80,
  }),
  columnHelper.accessor("read", {
    header: "Readers",
    cell: (info) => info.getValue(),
    sortingFn: "basic",
  }),
  columnHelper.accessor("narrative", {
    header: "Narrative",
    cell: (info) => info.getValue(),
    filterFn: equalsAny,
    sortingFn: "basic",
    size: 140,
  }),
  columnHelper.accessor("shelves", {
    header: "Shelves",
    cell: (info) => info.getValue().join(", "),
    filterFn: arrIncludesAny,
    sortingFn: "text",
    minSize: 200,
  }),
  columnHelper.accessor("number_of_pages", {
    header: "# of Pages",
    cell: (info) => info.getValue(),
    filterFn: equalsAny,
    sortingFn: "basic",
    size: 140,
  }),
];

export default function BooksDataTable({ url }: Props) {
  const { data, error, isLoading } = useSWR<Book[]>(url, fetcher);

  const table = useReactTable({
    data: data ?? [],
    columns: mainColumns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    initialState: {
      pagination: {
        pageIndex: 0,
        pageSize: 25,
      },
    },
  });

  const [authorRowSelection, setAuthorRowSelection] =
    useState<RowSelectionState>({});
  const [genderRowSelection, setGenderRowSelection] =
    useState<RowSelectionState>({});
  const [nationalityRowSelection, setNationalityRowSelection] =
    useState<RowSelectionState>({});
  const [yearRowSelection, setYearRowSelection] = useState<RowSelectionState>(
    {},
  );
  const [narrativeRowSelection, setNarrativeRowSelection] =
    useState<RowSelectionState>({});
  const [shelvesRowSelection, setShelvesRowSelection] =
    useState<RowSelectionState>({});
  const [pageCountRowSelection, setPageCountRowSelection] =
    useState<RowSelectionState>({});

  const [filtersCollapsed, setFiltersCollapsed] = useState(false);

  const activeFilterCount = sumBy(
    table.getState().columnFilters,
    ({ value }) => (value as string[] | null)?.length ?? 0,
  );

  if (error) {
    return <div>failed to load</div>;
  }
  if (isLoading) {
    return (
      <img
        src="/static/novelty/N-Logo-loop.gif"
        alt="Loading"
        className="mx-auto h-96"
      />
    );
  }
  if (!data) {
    return <div>No data</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex gap-x-4 mx-2 text-xs items-center">
        <span>Filters Active: {activeFilterCount}</span>
        <Button
          size="compact-sm"
          variant="default"
          leftSection={
            <div className="rotate-45">
              {filtersCollapsed ? (
                <IconArrowsDiagonal2 size={16} />
              ) : (
                <IconArrowsDiagonalMinimize size={16} />
              )}
            </div>
          }
          onClick={() => setFiltersCollapsed(!filtersCollapsed)}
        >
          {filtersCollapsed ? "Show All" : "Collapse All"}
        </Button>
        <Button
          size="compact-sm"
          variant="default"
          disabled={activeFilterCount === 0}
          rightSection={<IconX />}
          onClick={() => {
            setAuthorRowSelection({});
            setGenderRowSelection({});
            setNationalityRowSelection({});
            setYearRowSelection({});
            setNarrativeRowSelection({});
            setShelvesRowSelection({});
            setPageCountRowSelection({});
          }}
        >
          Clear All
        </Button>
      </div>
      <div className="flex">
        <ValueFilterTable<Book, string>
          table={table}
          columnId="author"
          collapsed={filtersCollapsed}
          rowSelection={authorRowSelection}
          setRowSelection={setAuthorRowSelection}
        />
        <ValueFilterTable<Book, string>
          table={table}
          columnId="gender"
          collapsed={filtersCollapsed}
          rowSelection={genderRowSelection}
          setRowSelection={setGenderRowSelection}
        />
        <ValueFilterTable<Book, string>
          table={table}
          columnId="nationality_chosen"
          collapsed={filtersCollapsed}
          rowSelection={nationalityRowSelection}
          setRowSelection={setNationalityRowSelection}
        />
        <ValueFilterTable<Book, number>
          table={table}
          columnId="original_publication_year"
          collapsed={filtersCollapsed}
          rowSelection={yearRowSelection}
          setRowSelection={setYearRowSelection}
        />
      </div>
      <div className="flex">
        <ValueFilterTable<Book, string>
          table={table}
          columnId="narrative"
          collapsed={filtersCollapsed}
          rowSelection={narrativeRowSelection}
          setRowSelection={setNarrativeRowSelection}
        />
        <ValueFilterTable<Book, string[]>
          table={table}
          columnId="shelves"
          collapsed={filtersCollapsed}
          rowSelection={shelvesRowSelection}
          setRowSelection={setShelvesRowSelection}
        />
        <ValueFilterTable<Book, number>
          table={table}
          columnId="number_of_pages"
          collapsed={filtersCollapsed}
          rowSelection={pageCountRowSelection}
          setRowSelection={setPageCountRowSelection}
        />
      </div>

      <DataTable table={table} pagination />
    </div>
  );
}
