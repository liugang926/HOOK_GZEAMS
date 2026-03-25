export function snakeToCamel(value: string): string {
  return value.replace(/_([a-zA-Z0-9])/g, (_m, chr: string) => chr.toUpperCase())
}

export function camelToSnake(value: string): string {
  return value
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/([A-Z])([A-Z][a-z])/g, '$1_$2')
    .toLowerCase()
}

