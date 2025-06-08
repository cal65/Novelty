import {
  type CellContext,
  type RowSelectionState,
  type SortingFnOption,
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import "@tanstack/react-table";
import { Button } from "@mantine/core";
import {
  IconArrowsDiagonal2,
  IconArrowsDiagonalMinimize,
  IconX,
} from "@tabler/icons-react";
import { type SetStateAction, useReducer, useState } from "react";
import { isFunction, sumBy } from "remeda";
import useSWR from "swr";
import { fetcher } from "../util/fetcher.ts";
import { saveToCsv } from "../util/tables.ts";
import DataTable from "./DataTable.tsx";
import { PageSizeControl } from "./PageSizeControl.tsx";
import SearchInput from "./SearchInput.tsx";
import ValueFilterTable from "./ValueFilterTable.tsx";
import { arrIncludesAny, equalsAny } from "./filterFunctions.ts";

type Props = {
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

const commonColumnFields = {
  cell: function value<TValue>(info: CellContext<Book, TValue>) {
    return info.getValue();
  },
  filterFn: equalsAny,
  sortingFn: "basic" as SortingFnOption<Book>,
};

const mainColumns = [
  columnHelper.accessor("title_simple", {
    ...commonColumnFields,
    header: "Title",
    minSize: 300,
    sortingFn: "alphanumeric",
  }),
  columnHelper.accessor("author", {
    ...commonColumnFields,
    header: "Author",
    sortingFn: "text",
  }),
  columnHelper.accessor("gender", {
    ...commonColumnFields,
    header: "Gender",
    size: 80,
  }),
  columnHelper.accessor("nationality_chosen", {
    ...commonColumnFields,
    header: "Nationality",
  }),
  columnHelper.accessor("original_publication_year", {
    ...commonColumnFields,
    header: "Year",
    size: 80,
  }),
  columnHelper.accessor("read", {
    ...commonColumnFields,
    header: "Readers",
  }),
  columnHelper.accessor("narrative", {
    ...commonColumnFields,
    header: "Narrative",
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
    ...commonColumnFields,
    header: "# of Pages",
    size: 140,
  }),
];

type FilterId =
  | "author"
  | "gender"
  | "nationality"
  | "year"
  | "narrative"
  | "shelves"
  | "pageCount";

type RowSelectionAction = FilterId | "clear";

function initialRowSelectionState(): Record<FilterId, RowSelectionState> {
  return {
    author: {},
    gender: {},
    nationality: {},
    year: {},
    narrative: {},
    shelves: {},
    pageCount: {},
  };
}

function rowSelectionReducer(
  state: Record<FilterId, RowSelectionState>,
  action: {
    type: RowSelectionAction;
    selection?: SetStateAction<RowSelectionState>;
  },
) {
  if (action.type === "clear") {
    return initialRowSelectionState();
  }
  return {
    ...state,
    [action.type]: isFunction(action.selection)
      ? action.selection(state[action.type])
      : action.selection,
  };
}

export default function BooksDataTable({ url }: Props) {
  const { data, error, isLoading } = useSWR<Book[]>(url, fetcher);

  const table = useReactTable({
    data: data ?? [],
    columns: mainColumns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    globalFilterFn: "auto",
    initialState: {
      pagination: {
        pageIndex: 0,
        pageSize: 25,
      },
    },
  });

  const [rowSelectionState, dispatchRowSelection] = useReducer(
    rowSelectionReducer,
    initialRowSelectionState(),
  );

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
    <div className="mx-2 space-y-6">
      <div className="flex gap-x-4 text-xs items-center">
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
          onClick={() => dispatchRowSelection({ type: "clear" })}
        >
          Clear All
        </Button>
      </div>
      <div className="grid gap-6 grid-cols-4">
        <ValueFilterTable<Book, string>
          table={table}
          columnId="author"
          collapsed={filtersCollapsed}
          rowSelection={rowSelectionState.author}
          setRowSelection={(selectedRows) =>
            dispatchRowSelection({ type: "author", selection: selectedRows })
          }
        />
        <ValueFilterTable<Book, string>
          table={table}
          columnId="gender"
          collapsed={filtersCollapsed}
          rowSelection={rowSelectionState.gender}
          setRowSelection={(selectedRows) =>
            dispatchRowSelection({ type: "gender", selection: selectedRows })
          }
        />
        <ValueFilterTable<Book, string>
          table={table}
          columnId="nationality_chosen"
          collapsed={filtersCollapsed}
          rowSelection={rowSelectionState.nationality}
          setRowSelection={(selectedRows) =>
            dispatchRowSelection({
              type: "nationality",
              selection: selectedRows,
            })
          }
        />
        <ValueFilterTable<Book, number>
          table={table}
          columnId="original_publication_year"
          collapsed={filtersCollapsed}
          rowSelection={rowSelectionState.year}
          setRowSelection={(selectedRows) =>
            dispatchRowSelection({ type: "year", selection: selectedRows })
          }
        />
        <ValueFilterTable<Book, string>
          table={table}
          columnId="narrative"
          collapsed={filtersCollapsed}
          rowSelection={rowSelectionState.narrative}
          setRowSelection={(selectedRows) =>
            dispatchRowSelection({ type: "narrative", selection: selectedRows })
          }
        />
        <ValueFilterTable<Book, string[]>
          table={table}
          columnId="shelves"
          collapsed={filtersCollapsed}
          rowSelection={rowSelectionState.shelves}
          setRowSelection={(selectedRows) =>
            dispatchRowSelection({ type: "shelves", selection: selectedRows })
          }
        />
        <ValueFilterTable<Book, number>
          table={table}
          columnId="number_of_pages"
          collapsed={filtersCollapsed}
          rowSelection={rowSelectionState.pageCount}
          setRowSelection={(selectedRows) =>
            dispatchRowSelection({ type: "pageCount", selection: selectedRows })
          }
        />
      </div>

      <div className="flex justify-between">
        <div className="flex gap-x-4 items-center">
          <PageSizeControl table={table} />

          <Button
            variant="default"
            onClick={() => saveToCsv(table, "books_data.csv")}
          >
            CSV
          </Button>
        </div>

        <SearchInput
          placeholder="Search all fields"
          value={table.getState().globalFilter ?? ""}
          onChange={(value) => table.setGlobalFilter(value)}
        />
      </div>

      <DataTable table={table} />
    </div>
  );
}
