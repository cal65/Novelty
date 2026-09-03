import { Select } from "@mantine/core";
import type { Table } from "@tanstack/react-table";
import { updatePageSize } from "../util/tables.ts";

type Props<TData> = {
  table: Table<TData>;
};

export function PageSizeControl<TData>({ table }: Props<TData>) {
  const { pagination } = table.getState();
  return (
    <div className="flex gap-x-1 items-center">
      Show
      <div className="w-24">
        <Select
          data={["10", "25", "50", "100"]}
          value={String(pagination.pageSize)}
          onChange={(value) => updatePageSize(table, value)}
        />
      </div>
      entries
    </div>
  );
}
