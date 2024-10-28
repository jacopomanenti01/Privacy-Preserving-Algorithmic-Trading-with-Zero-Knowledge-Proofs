USE db;

CREATE TABLE orders (
    id INT NOT NULL,
    createTime TIMESTAMP NOT NULL,
    instrument VARCHAR(10) NOT NULL, 
    price FLOAT(53) NOT NULL, 
    state VARCHAR(10) NOT NULL,
    stopLoss FLOAT(53) NOT NULL,
    takeprofit FLOAT(53) NOT NULL,
    units INT NOT NULL,
    PRIMARY KEY (id)
);