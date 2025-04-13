// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

contract Migrations {
  address public owner = msg.sender;
  uint public last_completed_migration;

  modifier restricted() {
    require(msg.sender == owner, "Restricted to owner");
    _;
  }

  function setCompleted(uint completed) public restricted {
    last_completed_migration = completed;
  }
}