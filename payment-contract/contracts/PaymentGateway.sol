// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PaymentGateway {
    address public owner;
    
    // Mapping to track registered merchants
    mapping(address => bool) public merchants;
    
    // Mapping to track processed payments
    mapping(string => bool) public processedPayments;
    
    // Events
    event PaymentProcessed(
        address indexed merchant,
        address indexed payer,
        uint256 amount,
        string indexed paymentId
    );
    
    event MerchantAdded(
        address indexed merchant,
        address indexed addedBy
    );
    
    event MerchantRemoved(
        address indexed merchant,
        address indexed removedBy
    );
    
    // Constructor
    constructor() {
        owner = msg.sender;
        // Register the owner as the first merchant
        merchants[owner] = true;
        emit MerchantAdded(owner, owner);
    }
    
    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    // Add a new merchant
    function addMerchant(address merchant) external onlyOwner {
        require(merchant != address(0), "Invalid merchant address");
        require(!merchants[merchant], "Merchant already registered");
        
        merchants[merchant] = true;
        emit MerchantAdded(merchant, msg.sender);
    }
    
    // Remove a merchant
    function removeMerchant(address merchant) external onlyOwner {
        require(merchants[merchant], "Merchant not registered");
        require(merchant != owner, "Cannot remove owner as merchant");
        
        merchants[merchant] = false;
        emit MerchantRemoved(merchant, msg.sender);
    }
    
    // Process a payment
    function processPayment(address payable merchant, string memory paymentId) external payable {
        require(merchants[merchant], "Merchant not registered");
        require(!processedPayments[paymentId], "Payment ID already processed");
        require(msg.value > 0, "Payment amount must be greater than 0");
        
        // Mark payment as processed
        processedPayments[paymentId] = true;
        
        // Transfer funds to merchant
        (bool sent, ) = merchant.call{value: msg.value}("");
        require(sent, "Failed to send Ether");
        
        // Emit payment event
        emit PaymentProcessed(merchant, msg.sender, msg.value, paymentId);
    }
    
    // Check if a payment has been processed
    function isPaymentProcessed(string memory paymentId) external view returns (bool) {
        return processedPayments[paymentId];
    }
    
    // Get contract balance (for debugging)
    function getContractBalance() external view onlyOwner returns (uint256) {
        return address(this).balance;
    }
}