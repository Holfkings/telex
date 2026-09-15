// @ts-nocheck
const chalk = require("chalk");

export function printSuccess(msg: string) {
  console.log(chalk.green(msg));
}
