// 7-color E-Ink Palette
const PALETTE = [
    [0,   0,   0],     // Black
    [255, 255, 255],   // White
    [0,   128, 0],     // Green
    [0,   0,   128],   // Blue
    [200, 0,   0],     // Red
    [255, 255, 0],     // Yellow
    [255, 128, 0],     // Orange
];

function colorDistanceSq(c1, c2) {
    return (c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2;
}

function findNearestColor(r, g, b) {
    let minDist = Infinity;
    let closest = PALETTE[0];
    for (let c of PALETTE) {
        let dist = colorDistanceSq([r, g, b], c);
        if (dist < minDist) {
            minDist = dist;
            closest = c;
        }
    }
    return closest;
}

self.onmessage = function(e) {
    const { imageData, width, height } = e.data;
    const data = new Uint8ClampedArray(imageData.data); // Copy data
    
    // Floyd-Steinberg Dithering
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = (y * width + x) * 4;
            const oldR = data[idx];
            const oldG = data[idx+1];
            const oldB = data[idx+2];
            
            const newColor = findNearestColor(oldR, oldG, oldB);
            
            data[idx] = newColor[0];
            data[idx+1] = newColor[1];
            data[idx+2] = newColor[2];
            // alpha is unchanged
            
            const errR = oldR - newColor[0];
            const errG = oldG - newColor[1];
            const errB = oldB - newColor[2];
            
            // Distribute error
            if (x + 1 < width) {
                let i = (y * width + (x + 1)) * 4;
                data[i]   = Math.min(255, Math.max(0, data[i]   + errR * 7/16));
                data[i+1] = Math.min(255, Math.max(0, data[i+1] + errG * 7/16));
                data[i+2] = Math.min(255, Math.max(0, data[i+2] + errB * 7/16));
            }
            if (x - 1 >= 0 && y + 1 < height) {
                let i = ((y + 1) * width + (x - 1)) * 4;
                data[i]   = Math.min(255, Math.max(0, data[i]   + errR * 3/16));
                data[i+1] = Math.min(255, Math.max(0, data[i+1] + errG * 3/16));
                data[i+2] = Math.min(255, Math.max(0, data[i+2] + errB * 3/16));
            }
            if (y + 1 < height) {
                let i = ((y + 1) * width + x) * 4;
                data[i]   = Math.min(255, Math.max(0, data[i]   + errR * 5/16));
                data[i+1] = Math.min(255, Math.max(0, data[i+1] + errG * 5/16));
                data[i+2] = Math.min(255, Math.max(0, data[i+2] + errB * 5/16));
            }
            if (x + 1 < width && y + 1 < height) {
                let i = ((y + 1) * width + (x + 1)) * 4;
                data[i]   = Math.min(255, Math.max(0, data[i]   + errR * 1/16));
                data[i+1] = Math.min(255, Math.max(0, data[i+1] + errG * 1/16));
                data[i+2] = Math.min(255, Math.max(0, data[i+2] + errB * 1/16));
            }
        }
    }
    
    const processedImageData = new ImageData(data, width, height);
    self.postMessage({ processed: processedImageData });
};
