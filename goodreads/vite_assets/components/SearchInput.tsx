import { CloseButton, type MantineSize, TextInput } from "@mantine/core";
import { IconSearch } from "@tabler/icons-react";
import clsx from "clsx";

type Props = {
  placeholder?: string;
  size?: MantineSize | string;
  onChange: (value: string | null) => void;
  value: string;
};

export default function SearchInput({
  placeholder = "Search",
  size = "xs",
  onChange,
  value,
}: Props) {
  return (
    <TextInput
      placeholder={placeholder}
      size={size}
      value={value}
      onChange={(e) => onChange(e.currentTarget.value)}
      leftSectionPointerEvents="none"
      leftSection={<IconSearch />}
      rightSection={
        <div className={clsx(!value && "hidden")}>
          <CloseButton iconSize="50%" onClick={() => onChange(null)} />
        </div>
      }
    />
  );
}
