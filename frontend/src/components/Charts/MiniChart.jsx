/**
 * Mini Chart Component - Sparkline style
 */
import React, { useEffect, useRef } from "react";

const MiniChart = ({ data = [], color = "#3b82f6", height = 60 }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || data.length < 2) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const chartHeight = canvas.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, chartHeight);

    // Calculate bounds
    const values = data.map((d) =>
      typeof d === "number" ? d : d.value || d.close || 0
    );
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    // Draw gradient area
    const gradient = ctx.createLinearGradient(0, 0, 0, chartHeight);
    gradient.addColorStop(0, color + "40");
    gradient.addColorStop(1, color + "00");

    ctx.beginPath();
    ctx.moveTo(0, chartHeight);

    values.forEach((value, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = chartHeight - ((value - min) / range) * (chartHeight - 10) - 5;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.lineTo(width, chartHeight);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw line
    ctx.beginPath();
    values.forEach((value, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = chartHeight - ((value - min) / range) * (chartHeight - 10) - 5;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();

    // Draw end dot
    const lastX = width;
    const lastY =
      chartHeight -
      ((values[values.length - 1] - min) / range) * (chartHeight - 10) -
      5;
    ctx.beginPath();
    ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.beginPath();
    ctx.arc(lastX, lastY, 6, 0, Math.PI * 2);
    ctx.strokeStyle = color + "40";
    ctx.lineWidth = 2;
    ctx.stroke();
  }, [data, color, height]);

  return (
    <canvas
      ref={canvasRef}
      width={200}
      height={height}
      className="w-full"
      style={{ height: `${height}px` }}
    />
  );
};

export default MiniChart;
