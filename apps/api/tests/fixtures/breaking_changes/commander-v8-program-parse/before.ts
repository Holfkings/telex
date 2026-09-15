// @ts-nocheck
import { program } from "commander";

export function getCliPort(): string {
  program.option("-p, --port <number>", "server port").parse(process.argv);
  return (program as any).port;
}
